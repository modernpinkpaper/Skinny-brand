"""The overall look / colouring you can choose. Each look says:
  themes  - extra searches that tend to find clips with that feel
  good/bad - what CLIP (the image checker) should prefer / avoid
  target  - wanted (brightness, colour strength), both 0..1, or None for "don't care"
  grade   - ffmpeg colour grade put on every clip so they all match"""

LOOKS = {
    "moody": dict(
        label="Moody / muted (darker, soft colours)",
        themes=["sad rain", "night window", "alone room", "lonely", "sunset sad", "train window", "walking alone night",
                "city night lights", "crying", "looking at sky", "hug", "memories", "quiet", "tears", "healing"],
        good=["a moody, dim scene with muted colours", "a quiet melancholic frame at night or dusk",
              "a soft, desaturated, cinematic scene"],
        bad=["a bright, colourful, cheerful scene", "a sticker on a white background", "a neon, saturated, loud image"],
        target=(0.38, 0.28),
        grade="eq=saturation=0.72:brightness=-0.035:contrast=1.06:gamma=0.95,vignette=PI/5"),
    "bright": dict(
        label="Bright & colourful",
        themes=["happy", "sunny day", "dancing", "laughing", "colorful", "friends fun", "celebration", "summer",
                "excited", "smile"],
        good=["a bright, colourful, cheerful scene", "vivid saturated colours on a sunny day"],
        bad=["a dark, gloomy, dim scene", "a black and white image"],
        target=(0.62, 0.55),
        grade="eq=saturation=1.12:contrast=1.03"),
    "vintage": dict(
        label="Warm vintage / nostalgic",
        themes=["retro", "vintage", "nostalgic", "old film", "autumn", "golden hour", "90s", "memories", "cozy"],
        good=["a warm, nostalgic, vintage film look with golden tones", "an old grainy retro scene"],
        bad=["a cold blue neon scene", "a sticker on a white background"],
        target=(0.5, 0.35),
        grade="colorbalance=rs=0.06:gs=0.02:bs=-0.06:rm=0.04:bm=-0.04,eq=saturation=0.85:contrast=0.95,vignette=PI/5"),
    "bw": dict(
        label="Black & white",
        themes=["black and white", "noir", "monochrome", "old movie", "silent film", "sad", "alone"],
        good=["a black and white image", "a monochrome film scene"],
        bad=["a colourful image"],
        target=(0.45, 0.02),
        grade="hue=s=0,eq=contrast=1.08"),
    "pastel": dict(
        label="Soft pastel / dreamy",
        themes=["dreamy", "soft pastel", "clouds", "flowers", "cute", "spring", "sky", "peaceful"],
        good=["a soft, dreamy scene in light pastel colours", "gentle pastel colours and soft light"],
        bad=["a dark, gloomy scene", "harsh neon colours"],
        target=(0.68, 0.25),
        grade="eq=saturation=0.85:brightness=0.03:gamma=1.05"),
    "none": dict(
        label="No preference",
        themes=["emotional", "feelings", "thinking", "walking", "friends", "love"],
        good=None, bad=None, target=None, grade=""),
}
