import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]


def execute(name, replies=(), env=None, opener_error=None):
    responses = [io.BytesIO(json.dumps(item).encode()) if not isinstance(item, Exception) else item for item in replies]
    output = io.StringIO()
    with patch.dict(os.environ, env or {}, clear=True), contextlib.redirect_stdout(output), \
            patch('urllib.request.urlopen', side_effect=responses) as request, \
            patch('urllib.request.OpenerDirector.open', side_effect=opener_error or AssertionError('unexpected network')) as opener, \
            patch('time.sleep'):
        try:
            runpy.run_path(str(ROOT / name), run_name='__main__')
            code = 0
        except SystemExit as error:
            code = error.code or 0
    return code, output.getvalue(), request, opener


class Checkins(unittest.TestCase):
    def test_missing_credentials_fail_without_network(self):
        for name in ('ctrip_checkin.py', 'cloud189_checkin.py', 'smzdm_checkin.py', 'smzdm_rewards.py', 'tieba_checkin.py'):
            with self.subTest(name=name):
                code, _, request, opener = execute(name)
                self.assertEqual(code, 1)
                request.assert_not_called()
                opener.assert_not_called()

    def test_ctrip_success(self):
        code, output, _, _ = execute('ctrip_checkin.py', [{'code': 0, 'continueDay': 6, 'baseIntegratedPoint': 12}], {'CTRIP_COOKIE': 'unit-test-cookie'})
        self.assertEqual(code, 0)
        self.assertIn('12', output)
        self.assertNotIn('unit-test-cookie', output)

    def test_ctrip_already_signed(self):
        code, _, _, _ = execute('ctrip_checkin.py', [{'code': 1, 'message': '今日已签到'}], {'CTRIP_COOKIE': 'unit-test-cookie'})
        self.assertEqual(code, 0)

    def test_ctrip_expired_cookie(self):
        code, output, _, _ = execute('ctrip_checkin.py', [HTTPError('https://m.ctrip.com/', 401, 'Unauthorized', {}, io.BytesIO())], {'CTRIP_COOKIE': 'unit-test-cookie'})
        self.assertEqual(code, 1)
        self.assertIn('401', output)

    def test_cloud_new_and_legacy_credentials(self):
        for env in ({'CLOUD189_USERNAME': 'unit-test-user', 'CLOUD189_PASSWORD': 'unit-test-password'},
                    {'CLOUD189_ACCOUNT': json.dumps({'username': 'unit-test-user', 'password': 'unit-test-password'})}):
            with self.subTest(keys=list(env)):
                code, output, _, opener = execute('cloud189_checkin.py', env=env,
                    opener_error=HTTPError('https://m.cloud.189.cn/login', 401, 'Unauthorized', {}, io.BytesIO()))
                self.assertEqual(code, 1)
                opener.assert_called_once()
                self.assertIn('401', output)
                self.assertNotIn('unit-test-password', output)

    def test_cloud_incomplete_or_invalid_account(self):
        for env in ({'CLOUD189_USERNAME': 'unit-test-user'}, {'CLOUD189_ACCOUNT': '[]'}, {'CLOUD189_ACCOUNT': '{'}):
            code, _, request, opener = execute('cloud189_checkin.py', env=env)
            self.assertEqual(code, 1)
            request.assert_not_called()
            opener.assert_not_called()

    def test_smzdm_captcha_is_not_success(self):
        code, output, _, _ = execute('smzdm_checkin.py', [{'error_code': 110202, 'error_msg': '验证码输入错误'}], {'SMZDM_COOKIE': 'unit-test-cookie'})
        self.assertEqual(code, 1)
        self.assertIn('验证码', output)

    def test_smzdm_already_signed(self):
        code, _, _, _ = execute('smzdm_checkin.py', [{'error_code': 1, 'error_msg': '今日已签到'}], {'SMZDM_COOKIE': 'unit-test-cookie'})
        self.assertEqual(code, 0)

    def test_rewards_does_not_post_or_follow(self):
        tasks = [{'task_name': event, 'task_status': 2, 'task_event_type': event} for event in ('interactive.comment', 'interactive.follow.user', 'publish.baoliao_new')]
        reply = {'error_code': 0, 'data': {'rows': [{'cell_data': {'activity_task': {'default_list_v2': [{'task_list': tasks}]}}}]}}
        code, output, request, _ = execute('smzdm_rewards.py', [reply], {'SMZDM_COOKIE': 'unit-test-cookie'})
        self.assertEqual(code, 0)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(output.count('待人工完成类型'), 3)

    def test_rewards_unknown_response_fails(self):
        code, output, _, _ = execute('smzdm_rewards.py', [{'error_code': 0, 'data': {}}], {'SMZDM_COOKIE': 'unit-test-cookie'})
        self.assertEqual(code, 1)
        self.assertIn('结构已变化', output)

    def test_tieba_reports_success_and_skip(self):
        code, output, _, _ = execute('tieba_checkin.py', [{'is_login': 1, 'tbs': 'unit-test'}, {'no': 0}, {'no': 1011}], {'TIEBA_COOKIE': 'unit-test-cookie', 'TIEBA_FORUMS': 'one,two'})
        self.assertEqual(code, 0)
        self.assertIn('成功 1，跳过 1，失败 0', output)

    def test_tieba_all_skipped_is_not_success(self):
        code, output, _, _ = execute('tieba_checkin.py', [{'is_login': 1, 'tbs': 'unit-test'}, {'no': 1011}], {'TIEBA_COOKIE': 'unit-test-cookie', 'TIEBA_FORUMS': 'one'})
        self.assertEqual(code, 1)
        self.assertIn('成功 0，跳过 1', output)

    def test_tieba_unexpected_error_stays_failed(self):
        code, _, _, _ = execute('tieba_checkin.py', [{'is_login': 1, 'tbs': 'unit-test'}, {'no': 999}], {'TIEBA_COOKIE': 'unit-test-cookie', 'TIEBA_FORUMS': 'one'})
        self.assertEqual(code, 1)

    def test_tieba_forums_are_required_and_deduplicated(self):
        code, _, request, _ = execute('tieba_checkin.py', env={'TIEBA_COOKIE': 'unit-test-cookie'})
        self.assertEqual(code, 1)
        request.assert_not_called()
        code, _, request, _ = execute('tieba_checkin.py', [{'is_login': 1, 'tbs': 'unit-test'}, {'no': 0}], {'TIEBA_COOKIE': 'unit-test-cookie', 'TIEBA_FORUMS': ' one,one, ,'})
        self.assertEqual(code, 0)
        self.assertEqual(request.call_count, 2)


if __name__ == '__main__':
    unittest.main()
