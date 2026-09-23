// Photo library used by the posts. Each photo is generated once (Canva AI image) and saved as social/photos/<key>.jpg
// Style rule for every prompt: real-looking iPhone photo, vertical 9:16, natural light, healthy slim/fit women (never frail),
// no text in the image.
const STYLE = "realistic candid iPhone photo, vertical 9:16, natural light, soft film grain, warm pastel tones, no text, no logos";

export const PHOTOS = {
  crying:        `young woman sitting on her bed crying, mascara smudged, holding her phone, moody evening bedroom light, ${STYLE}`,
  fridge_night:  `young woman in pajamas standing in a dark kitchen at night, face lit by the open fridge light, looking inside, ${STYLE}`,
  mirror_jeans:  `slim healthy young woman in high-waisted jeans and a white crop top smiling at herself in a full-length mirror, bright apartment, ${STYLE}`,
  coffee_walk:   `slim confident young woman walking on a city street holding an iced coffee, morning sun, flowy outfit, ${STYLE}`,
  shocked_phone: `young woman staring at her phone in shock, hand over her mouth, sitting on a couch, ${STYLE}`,
  eye_roll:      `sassy young woman rolling her eyes with arms crossed, pink sweater, cream wall background, ${STYLE}`,
  breakfast:     `young woman eating scrambled eggs and greek yogurt with berries at a sunny kitchen table, smiling, ${STYLE}`,
  restaurant:    `three stylish young women laughing at a restaurant dinner table with drinks, warm evening light, ${STYLE}`,
  lifting:       `fit young woman doing a goblet squat with a dumbbell in her living room, leggings and sports bra, focused, ${STYLE}`,
  bed_scroll:    `young woman lying in bed at night scrolling her phone, blue screen glow on her face, dark room, ${STYLE}`,
  smoothie:      `slim fit young woman in pastel activewear holding a pink smoothie in a bright kitchen, ${STYLE}`,
  dress_event:   `confident slim young woman in a fitted black dress getting ready in front of a mirror, fairy lights, ${STYLE}`,
  scale_shock:   `young woman standing on a bathroom scale looking down, surprised worried face, white bathroom, ${STYLE}`,
  grocery:       `young woman in a grocery store produce aisle holding a bag of vegetables, casual chic outfit, ${STYLE}`,
  couch_snack:   `young woman on a couch caught eating chips straight from the bag, guilty funny face, TV glow, ${STYLE}`,
  golden_walk:   `slim confident young woman walking in a summer dress at golden hour, hair blowing, glowing and happy, ${STYLE}`,
  tea_night:     `young woman in a cozy robe holding a mug of herbal tea on the couch, calm evening lamp light, ${STYLE}`,
  besties:       `two young women friends laughing together on a couch looking at a phone, cozy apartment, ${STYLE}`,
  sad_window:    `young woman sitting by a rainy window looking sad and thoughtful, oversized sweater, ${STYLE}`,
  smirk:         `confident young woman smirking at the camera, slim, stylish neutral outfit, cream background, ${STYLE}`,
};
