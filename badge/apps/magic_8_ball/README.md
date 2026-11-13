# Magic 8 Ball

Shake your badge to turn over a Magic 8 Ball and reveal one of eight answers to your yes-or-no question.

## Usage

1. Open **Magic 8 Ball** from the menu and think of a yes-or-no question.
2. Give the badge a quick shake (a couple of firm back-and-forth flicks).
   The ball turns over and an answer floats up into the blue window.
3. The answer stays on screen until you ask again. Hold the badge still for a
   moment, then shake again for a new answer. Shaking continuously only
   produces one answer.
4. Press **SELECT** to ask without shaking (handy when the badge is on a
   lanyard or on a desk).

The eight answers are: "Most definitely!", "Seems doubtful", "Signs point to
yes", "Ask again later", "Without a doubt", "Don't count on it", "Outlook
good" and "My sources say no". The same answer is never given twice in a row.

## How shake detection works

The app reads the badge's built-in LSM6DS3TR-C accelerometer with
`badge.imu()` (about 16384 counts per g). A low-pass filter tracks gravity and
subtracts it, so tilting or turning the badge over slowly does not count as a
shake. Two separate jolts of more than 0.75 g within 0.7 seconds trigger an
answer. Detection then pauses until at least 0.9 seconds have passed and the
badge has been calm for 0.35 seconds. Tuning constants live in `oracle.py`.

## Requirements

No extra hardware, Wi-Fi or `secrets.py` settings are needed. It uses the
2026 badge firmware's `badge.imu()` and the MonaSans font in
`/system/assets/fonts` (falling back to a built-in font if it is missing).
