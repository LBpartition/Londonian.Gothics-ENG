"""Apply guide text that the original matcher missed (verbatim from ShadowRisae-Guide.txt, split to JP line order)."""
import json, sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]
F = W / "tools-resources" / "final"

PURIFY = "When the bordermoon collapses, the nearby miasma is purified."
M = {
 "sp_home004.sp": {
  22: "All righty. Wonder if there'll be anything here.",
  18: "*rummage, rummage*",
  11: "Nope, nothing relevant in here...",
  16: "Oh, what's this? Father's diary?",
  43: "Indeed it is. Invading his privacy would be uncouth, but, should I read a little of it?",
  24: "Well, I want any kind of clue I can find, so Father, I'm sorry about this.",
  23: "Although if I'm being honest it's exciting to find out what someone else writes in their private diary.",
  38: "Hehe. Let's dive in! Lessee here...",
  34: "April 5th:",
  0: "Today I took my daughter on an outing.",
  31: "How long has it been since I've seen her so pleased?",
  5: "April 13th:",
  36: "Today I played games with my daughter.",
  3: "Watching her expressions ebb and flow like the tide made me feel happy for some reason.",
  30: "April 21st:",
  2: "These enjoyable days quietly pass one after the next. I hope life can continue to be like this....",
  14: "Oh Father, you had me in your thoughts that much?",
  40: "I feel tears coming on... *sniff*",
  25: "Ahem.",
  39: "Shall we continue reading?",
  20: "August 19th:",
  4: "Even after the exile, civil unrest in Russia has not been quelled.",
  19: "We remain safe for the time being, but I wonder how long that can last...",
  15: "October 23rd:",
  17: "The flowing sands of time can't be stopped, nor can the rise and fall of the eras.",
  41: "Something serious is bound to happen before long.",
  29: "December 2nd:",
  1: "A great many more people were killed today.",
  42: "If this keeps up I fear that we will be in serious danger. I've got to think of some way....",
  6: "......",
  27: "Huh? It ends there?!",
  7: "Oh phooey, just when it was getting to the good part.",
  10: "Sheesh. Isn't there any more?",
  44: "Nope, it looks like that's it for the desk.",
  21: "If there were more pages, where would they be? Maybe in Father's own room.. Worth a shot, right?",
  9: "But hold on, it said Father was Russian, no?",
  8: "How can that be? I don't have any memories of life in Russia myself.",
  12: "Did I just forget? Hmm, hmmm...",
  33: "Not happening. I can't pull a single one.",
  13: "Oh well. I'll have to worry about that later.",
  35: "Now back to the task at hand. I need to find out more about Father.",
 },
 "sp_home016.sp": {
  6: "Miss, what have you come here for?",
  37: "Just visiting.",
  4: "Since you've apparently got the time to dawdle about in my humble little room, how about you take your leave?",
  46: "If you don't hurry up the professor's surely going to.... kekekeke.",
  9: "D-don't say frightening things like that!",
  24: "And speaking of, that laugh creeps me out so it'd be great if you could put the kibosh on it.",
  29: "Goodness, how rude. What is the matter with you?",
  18: "Ah, er, well. I'm sorry.",
  7: "See here! Please stop idling about and make haste to go. The professor's waiting for you, no?",
  51: "O-okay I will.",
  47: "Oh my, Miss? What do you want?",
  2: "Don't tell me you've elected to abandon the professor after all.",
  14: "Huhuhu! I knew it, protecting your own life is more important than saving his.",
  45: "Oh, am I wrong?",
  30: "If so, how about you get going on the double? Before it's too late?",
  13: "Can't say I'd mind if you gave up on him though. Keeekkekekekeke.",
 },
 "sp109.sp": {
  26: ".......", 8: "Say something already.", 27: "You first.",
  18: "I don't have anything to talk about.", 10: "Me either.", 15: "I see.", 7: "Yup.",
 },
 "sp121.sp": {
  23: "Need something from me?", 2: "No, I don't.", 25: "........",
  13: "Oh that's unfortunate. I was hoping for company to help pass the time.",
  22: "That's great and all, but I still don't need anything.",
  21: "Do you need something?", 4: "I'm unfamiliar.",
  11: "When I'm not familiar with something all I can say is \"I'm unfamiliar\".",
  20: ".....Now that you mention it.",
  19: "I recall hearing that someone has added an unusual book to their shop inventory.",
  15: "Probably meaning a holy book, a bible.", 12: "Most likely.",
  9: "If I'm not mistaken it was on B26F....",
  17: "....I'm not exactly certain about that though.",
  6: "How about you go find out?",
 },
 "sp129.sp": {
  10: "Father, are you okay? Still with us?",
  5: "Ha ha ha ha. Oh, ohhh, Alice!",
  21: "Hang on! I'm getting you out of there!",
 },
 "sp132.sp": {
  0: "Haah, haah.", 14: "T-take that!",
  3: "But.... My body's.. giving out.. and it's really the end of the line for me too, it seems...",
 },
 "sp_home005.sp": {41: "......"},
}
for f, i in [("sp002.sp", 6), ("sp012.sp", 15), ("sp019.sp", 0), ("sp029.sp", 7), ("sp037.sp", 0),
             ("sp056.sp", 1), ("sp070.sp", 0), ("sp072.sp", 0), ("sp078.sp", 0), ("sp109.sp", 4), ("sp128.sp", 3)]:
    M.setdefault(f, {})[i] = PURIFY

n = 0
for f, m in M.items():
    p = F / (f + ".json"); d = json.loads(p.read_text(encoding="utf-8"))
    seen = set()
    for e in d:
        if e["idx"] in m:
            e["en"] = m[e["idx"]]; e["note"] = "guide (realigned)"; seen.add(e["idx"]); n += 1
    miss = set(m) - seen
    if miss: sys.exit(f"{f}: idx not found {miss}")
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("set", n, "entries")
