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


class SpeakerTests(unittest.TestCase):
    def test_speaks_complete_sentences_in_order(self):
        spoken = []
        with mock.patch.object(voice.shutil, "which", return_value="/usr/bin/say"), \
             mock.patch.object(voice, "_say", side_effect=spoken.append):
            s = voice.Speaker(enabled=True)
            for piece in ["Over", "loaded. Pick ", "one! Then", " rest"]:
                s.feed(piece)
            s.flush()
            s.close()
        self.assertEqual(spoken, ["Overloaded.", "Pick one!", "Then rest"])

    def test_disabled_speaker_is_silent(self):
        with mock.patch.object(voice, "_say") as say:
            s = voice.Speaker(enabled=False)
            s.feed("Hello. World.")
            s.flush()
            s.close()
        say.assert_not_called()


if __name__ == "__main__":
    unittest.main()
