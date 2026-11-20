import unittest
from unittest import mock

from vector import voice


class SpeakTests(unittest.TestCase):
    def test_text_goes_to_stdin_not_shell(self):
        payload = '$(touch /tmp/pwned) `id`; rm -rf ~'
        with mock.patch.object(voice.shutil, "which", return_value="/usr/bin/say"), \
             mock.patch.object(voice.config, "SPEAK", True), \
             mock.patch.object(voice.subprocess, "run") as run:
            voice.speak(payload)
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["say"])
        self.assertEqual(kwargs["input"], payload)
        self.assertNotIn("shell", kwargs)


if __name__ == "__main__":
    unittest.main()
