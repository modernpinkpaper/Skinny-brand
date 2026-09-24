// 21 TikTok posts: 7 days x 3 per day.
// Voice: first person, a normal girl sharing what worked for HER. casual, lowercase, not perfectly grammatical.
// Every post stands alone: provocative hook -> her story -> the one tip -> "i put it in a lil guide, its in my bio".
//
// Carousel slide types:
//   say   {img, text, y?}      her photo + plain white TikTok text box (y = how far down the text sits, 0-1)
//   notes / imsg              screenshot of her notes app / a text chat
//   vault {sel, text, tick?}  a phone screenshot of the actual guide, scrolled to a section, with a white text box
// Video types:
//   notes  typing in the notes app      imsg  back-and-forth text chat      demo  scrolling + tapping through the guide
//
// Photo keys = files in social/my-photos/named/. Keep ONE girl per carousel:
//   blonde:   cry_bed cry_laptop cry_car cry_grocery cry_gym cry_gym2 cry_gym3 cry_gym4 mirror_gym teeth
//   brunette: mirror_selfie coffee_car mirror_bathroom grocery package gas dog_walk store_line cooking laundry cafe_laptop
//   one-shot hooks (talking to camera): rant_kitchen rant_kitchen2..5 rant_car rant_car2..5

export const POSTS = [
// ───────────────────────── DAY 1 ─────────────────────────
{
  id: "d1-1-carousel-wish-i-knew", day: 1, time: "7:30 AM", format: "carousel",
  title: "3 years of heartache (crying hook)",
  slides: [
    { t: "say", img: "cry_bed", text: "i wasted 3 years crying over my body when the fix was literally this 😭", y: 0.14 },
    { t: "say", img: "cry_laptop", text: "i was \"good\" all day. coffee for breakfast, sad salad for lunch", y: 0.2 },
    { t: "say", img: "cry_car", text: "then 9pm hit and i'd eat the entire kitchen and hate myself for it. every night", y: 0.16 },
    { t: "say", img: "mirror_gym", text: "turns out i wasnt weak. i was just starving by night lol", y: 0.18 },
    { t: "say", img: "teeth", text: "now i eat like 30g protein before 10am (eggs, greek yogurt, whatever) and the 9pm snack attacks just… stopped", y: 0.12 },
    { t: "vault", sel: "#hack-1", text: "its literally the first thing in the lil guide i made bc it changed everything for me" },
  ],
  caption: "if u eat \"perfect\" all day and then lose it at night this is for u. i promise ur not weak 🤍",
  hashtags: "#nightsnacking #proteinbreakfast #iwishiknew #weightlosstips",
  pin: "the guide is in my bio if u want the other 119 things that helped me",
},
{
  id: "d1-2-video-imsg-latte", day: 1, time: "12:15 PM", format: "video",
  title: "bestie roasts my latte",
  video: { t: "imsg", name: "Bestie 💕", msgs: [
    { me: false, text: "i literally barely eat and i'm not losing anything" },
    { me: true, text: "what did u have today" },
    { me: false, text: "just my caramel iced latte and like a granola bar" },
    { me: true, text: "babe that latte has more sugar than a donut 😭" },
    { me: false, text: "STOP no it doesnt" },
    { me: true, text: "google it. i switched to 1 pump + milk and didnt even notice after 3 days" },
    { me: false, text: "i'm actually offended rn" },
    { me: true, text: "drinks dont fill u up so ur starving AND drinking dessert lol" },
  ] },
  onScreenHook: "my best friend \"barely eats\" 🙄",
  caption: "i was her. i was literally her ☕😭",
  hashtags: "#coffeeorder #themathaintmathing #relatable #weightlosstips",
  pin: "the coffee thing is in my lil guide too (bio) 🤍",
},
{
  id: "d1-3-carousel-food-order", day: 1, time: "8:00 PM", format: "carousel",
  title: "skinny girls eat in a different order",
  slides: [
    { t: "say", img: "rant_kitchen3", text: "skinny girls dont have more willpower than u. they just eat in a different ORDER", y: 0.13 },
    { t: "notes", title: "dinner rule 🥦", date: "Monday 6:48 PM", lines: ["1. veggies first", "2. then protein", "3. carbs LAST", "", "same plate. same food.", "u just get full faster + no crash later", "", "(i still eat the carbs dont worry lol)"] },
    { t: "vault", sel: "#hack-2", text: "theres actual studies on it, i put the why + how in my guide" },
  ],
  caption: "same food different order. try it at dinner tonight and tell me",
  hashtags: "#eatingtips #bloodsugar #skinnytips #healthyhabits",
  pin: "report back tomorrow 👀",
},
// ───────────────────────── DAY 2 ─────────────────────────
{
  id: "d2-1-video-notes-stopped-doing", day: 2, time: "7:30 AM", format: "video",
  title: "notes: things i stopped doing",
  video: { t: "notes", title: "things i stopped doing (and lost the weight without trying)", date: "Tuesday 7:12 AM", lines: [
    "- eating out of the bag",
    "- skipping breakfast to \"save calories\"",
    "- ordering last at restaurants",
    "- scrolling in bed till 1am",
    "- drinking my calories",
    "- starting over every monday",
    "",
    "none of it was a diet lol",
    "that's prob why it worked",
  ] },
  onScreenHook: "ok this is gonna sound dumb but",
  caption: "none of these feel like a diet which is exactly why they stuck 📝",
  hashtags: "#notesapp #thatgirlhabits #weightlosstips #healthyroutine",
  pin: "i explain every one of these in my guide (bio)",
},
{
  id: "d2-2-carousel-kitchen-closed", day: 2, time: "12:15 PM", format: "carousel",
  title: "if u snack at night read this",
  slides: [
    { t: "say", img: "cooking", text: "if u snack every night pls read this. i was the worst", y: 0.12 },
    { t: "say", img: "laundry", text: "dinner at 7, \"second dinner\" at 10:30, random toast at midnight. every. night.", y: 0.14 },
    { t: "say", img: "mirror_bathroom", text: "now i \"close\" my kitchen after dinner like a restaurant. wipe the counter, lights off, brush my teeth", y: 0.12 },
    { t: "say", img: "dog_walk", text: "nothing tastes good after mint so i just… dont. walk or tea on the couch and done", y: 0.14 },
    { t: "vault", sel: "#hack-14", text: "sounds so dumb but its the one ppl message me about the most" },
  ],
  caption: "my kitchen used to be open 24/7 like a diner 😭",
  hashtags: "#nightsnacking #nightroutine #kitchenclosed #thatgirl",
  pin: "be honest what time does ur kitchen close 😂",
},
{
  id: "d2-3-video-demo-finally-made-it", day: 2, time: "8:00 PM", format: "video",
  title: "demo: i finally finished it",
  video: { t: "demo", name: "finally-made-it" },
  caption: "ok i finally finished it 😭 every weird tip that actually worked for me in one place. idk if anyone needs this but here",
  hashtags: "#weightlosstips #skinnytips #healthyhabits #smallbusiness",
  pin: "its in my bio if u want it 🤍 took me forever lol",
},
// ───────────────────────── DAY 3 ─────────────────────────
{
  id: "d3-1-carousel-scale-car-cry", day: 3, time: "7:30 AM", format: "carousel",
  title: "cried in my car over the scale",
  slides: [
    { t: "say", img: "cry_car", text: "i cried in my car bc the scale said i gained 3 lbs overnight", y: 0.16 },
    { t: "say", img: "cry_grocery", text: "then i ate a whole pizza bc \"whats even the point\"", y: 0.14 },
    { t: "say", img: "mirror_gym", text: "it was WATER. salt, carbs, hormones. u literally cant gain 3 lbs of fat in a day", y: 0.15 },
    { t: "vault", sel: "#bonus-tracker", text: "now i only look at my weekly average. i put a lil tracker in my guide that does the math for me" },
  ],
  caption: "the scale isnt lying its just talking about water 💧 dont let one number ruin ur week like i did",
  hashtags: "#scale #waterweight #weightfluctuations #weightlossjourney",
  pin: "this honestly saved my sanity",
},
{
  id: "d3-2-video-imsg-order-first", day: 3, time: "12:15 PM", format: "video",
  title: "bestie asks how i eat out",
  video: { t: "imsg", name: "Maddie 🤍", msgs: [
    { me: false, text: "ok how do u eat out every weekend and still look like that" },
    { me: true, text: "i order first lol" },
    { me: false, text: "…what" },
    { me: true, text: "ppl copy the table. if u order last u end up getting the burger bc everyone did" },
    { me: false, text: "that cant be it" },
    { me: true, text: "and i pick ONE treat. drinks or bread or dessert. not all 3" },
    { me: false, text: "ok thats actually genius" },
    { me: true, text: "i know 💅" },
  ] },
  onScreenHook: "she asked so i told her",
  caption: "i still go out every weekend i just have a game plan now 💅",
  hashtags: "#eatingout #restauranthacks #girlsnight #skinnytips",
  pin: "tag the friend who always orders last and copies u 😂",
},
{
  id: "d3-3-carousel-smoothie", day: 3, time: "8:00 PM", format: "carousel",
  title: "ur smoothie is why ur starving",
  slides: [
    { t: "say", img: "rant_car", text: "ur not gonna like this but ur \"healthy\" smoothie is prob why ur starving by 10am", y: 0.13 },
    { t: "notes", title: "smoothie fix 🥤", date: "Wednesday 9:20 AM", lines: ["drinking fruit ≠ eating fruit", "3 bananas go down in like 90 sec", "", "what i do now:", "- add protein or greek yogurt", "- only 1 cup fruit", "- eat something crunchy with it", "", "full till lunch now. finally"] },
    { t: "vault", sel: "#hack-72", text: "its in my guide under the drink ones" },
  ],
  caption: "not saying quit ur smoothie. saying fix it 🥤",
  hashtags: "#smoothie #notgonnalikethis #proteinsmoothie #healthyhabits",
  pin: "did u know this?? 😳",
},
// ───────────────────────── DAY 4 ─────────────────────────
{
  id: "d4-1-video-notes-craving-wave", day: 4, time: "7:30 AM", format: "video",
  title: "notes: cravings are a wave",
  video: { t: "notes", title: "i just found out how cravings work 🤯", date: "Thursday 9:41 PM", lines: [
    "a craving is like a wave",
    "it builds… peaks… then goes away",
    "usually in like 10 min",
    "",
    "so now i say \"ok. in 10 minutes\"",
    "set a timer, make tea, text someone",
    "",
    "half the time i forget i even wanted it",
    "the other half i eat it slow and im fine",
  ] },
  onScreenHook: "omg i just found out",
  caption: "not \"never eat it\" just \"not this second\" 🕙 try it tonight",
  hashtags: "#cravings #ijustfoundout #sugarcravings #weightlosstips",
  pin: "tell me if it works for u 👇",
},
{
  id: "d4-2-carousel-not-the-gym", day: 4, time: "12:15 PM", format: "carousel",
  title: "what keeps me lean that isnt the gym",
  slides: [
    { t: "say", img: "coffee_car", text: "things that keep me lean that have nothing to do with the gym 👇", y: 0.14 },
    { t: "say", img: "dog_walk", text: "10 min walk after every meal. not a workout. just a walk", y: 0.14 },
    { t: "say", img: "grocery", text: "i never grocery shop hungry. ever. if its not in the house i cant eat it at 11pm", y: 0.13 },
    { t: "say", img: "laundry", text: "chores count lol. cleaning, laundry, walking calls. it adds up more than a gym session", y: 0.15 },
    { t: "say", img: "cooking", text: "and protein at every meal. thats kinda it", y: 0.14 },
    { t: "vault", sel: "#hack-32", text: "i wrote down everything that worked in my guide if u want the rest" },
  ],
  caption: "i thought i had a slow metabolism. i was just sitting all day 🪑😭",
  hashtags: "#lazygirlworkout #neat #walking #weightlosstips",
  pin: "the walk after dinner is non negotiable now",
},
{
  id: "d4-3-video-demo-search", day: 4, time: "8:00 PM", format: "video",
  title: "demo: search ur problem",
  video: { t: "demo", name: "search-your-problem" },
  caption: "my fav part is u can literally just search ur problem 😭 \"night\" gave me 20+ things to try",
  hashtags: "#nightsnacking #cravings #weightlosstips #skinnytips",
  pin: "link's in my bio. what would u search first? 👇",
},
// ───────────────────────── DAY 5 ─────────────────────────
{
  id: "d5-1-carousel-start-monday", day: 5, time: "7:30 AM", format: "carousel",
  title: "i'll start monday",
  slides: [
    { t: "say", img: "rant_kitchen", text: "\"i'll start monday\" has started 52 mondays a year babe. i would know", y: 0.14 },
    { t: "notes", title: "the loop i was stuck in", date: "Friday 8:05 AM", lines: ["be perfect", "eat one cookie", "\"welp day's ruined\"", "eat everything", "start over monday", "repeat forever 🙃", "", "what fixed it: never miss twice.", "one bad meal = fine. next meal is just normal.", "not skipped. not punished. normal."] },
    { t: "vault", sel: "#hack-81", text: "this one lives in my head rent free. its in my guide" },
  ],
  caption: "u dont need a fresh start monday. u need a normal next meal 🧠",
  hashtags: "#allornothing #mindset #nevermisstwice #weightlossjourney",
  pin: "save this for ur next \"i ruined it\" day 📌",
},
{
  id: "d5-2-video-imsg-bag", day: 5, time: "12:15 PM", format: "video",
  title: "not me eating from the bag",
  video: { t: "imsg", name: "Bestie 💕", msgs: [
    { me: false, text: "not me opening the chips for \"a few\"" },
    { me: false, text: "and now the bag is empty 🙃" },
    { me: true, text: "u ate from the bag didnt u" },
    { me: false, text: "…maybe" },
    { me: true, text: "put some in a bowl. put the bag AWAY. then sit down" },
    { me: false, text: "thats so simple its annoying" },
    { me: true, text: "a bag has no bottom. a bowl does 🥣" },
  ] },
  onScreenHook: "not me… again 🙃",
  caption: "a bag has no bottom. a bowl does 🥣",
  hashtags: "#notme #snacking #portioncontrol #relatable",
  pin: "be honest… bowl or bag 😂",
},
{
  id: "d5-3-carousel-math-aint-mathing", day: 5, time: "8:00 PM", format: "carousel",
  title: "the math aint mathing",
  slides: [
    { t: "say", img: "rant_car4", text: "the math aint mathing when u \"barely eat\" but…", y: 0.14 },
    { t: "notes", title: "things i said that were lies 💀", date: "Friday 7:58 PM", lines: ["\"i never snack\"", "(the handful of chips every time i walked past the kitchen)", "", "\"i eat so clean\"", "(3 tablespoons of peanut butter on a rice cake)", "", "\"i was good all week\"", "(brunch, 4 margs and a 2am drive thru)"] },
    { t: "vault", sel: "#hack-12", text: "anyway i fixed it without dieting. its all in my guide lol" },
  ],
  caption: "said with love bc i said every single one of these 😭",
  hashtags: "#themathaintmathing #snacking #relatable #weightlossjourney",
  pin: "which one exposed u 😂",
},
// ───────────────────────── DAY 6 ─────────────────────────
{
  id: "d6-1-video-notes-grocery", day: 6, time: "7:30 AM", format: "video",
  title: "notes: my grocery rules",
  video: { t: "notes", title: "grocery rules that keep me lean 🛒", date: "Saturday 10:03 AM", lines: [
    "- never shop hungry (eat first!!)",
    "- frozen aisle is my bff",
    "   veggies, berries, shrimp, edamame",
    "- rotisserie chicken = 3 meals",
    "- buy flavor not calories",
    "   hot sauce, salsa, lemon, seasoning",
    "- trigger snacks stay at the store",
    "",
    "if its not in the house i cant eat it at 11pm 🤷‍♀️",
  ] },
  onScreenHook: "steal my grocery rules",
  caption: "if its not in the house u cant eat it at 11pm 🤷‍♀️",
  hashtags: "#grocerytips #healthygrocery #mealprep #skinnytips",
  pin: "the full grocery list is in my guide (bio) 🛒",
},
{
  id: "d6-2-carousel-cardio-soft", day: 6, time: "12:15 PM", format: "carousel",
  title: "2 hours cardio and still soft",
  slides: [
    { t: "say", img: "cry_gym", text: "i did 2 hours of cardio a day and ate like a bird and still looked \"soft\"", y: 0.14 },
    { t: "say", img: "cry_gym4", text: "i was so mad. like what else do u want from me", y: 0.16 },
    { t: "say", img: "mirror_gym", text: "i was losing muscle not just fat. now i lift 2x a week (20 min!!) + protein every meal", y: 0.13 },
    { t: "vault", sel: "#hack-102", text: "the exact beginner plan is in my guide. its so much less than u think" },
  ],
  caption: "smaller isnt the goal. firm is 💪 and no u wont get bulky lol",
  hashtags: "#skinnyfat #strengthtraining #protein #gymgirl",
  pin: "2 short sessions a week. thats it",
},
{
  id: "d6-3-video-imsg-event", day: 6, time: "8:00 PM", format: "video",
  title: "should i just not eat before the wedding",
  video: { t: "imsg", name: "Sis 🌸", msgs: [
    { me: false, text: "wedding saturday. should i just not eat friday" },
    { me: true, text: "NO omg" },
    { me: true, text: "ull be cranky, puffy and then inhale the buffet" },
    { me: false, text: "ok then what" },
    { me: true, text: "normal meals. protein + cooked veggies. skip salty takeout" },
    { me: true, text: "banana or potato for potassium, no fizzy drinks or gum, walk after dinner" },
    { me: true, text: "and sleep early. u'll wake up way less bloated" },
    { me: false, text: "why do u know all this 😭" },
  ] },
  onScreenHook: "my sister was about to do something dumb",
  caption: "crash dieting before an event backfires every single time. do this instead ✨",
  hashtags: "#debloat #eventprep #bloating #glowup",
  pin: "the whole day-before plan is in my guide 🤍",
},
// ───────────────────────── DAY 7 ─────────────────────────
{
  id: "d7-1-carousel-eating-type", day: 7, time: "7:30 AM", format: "carousel",
  title: "which one are u be honest",
  slides: [
    { t: "say", img: "rant_kitchen4", text: "ok which one are u. be honest 👀", y: 0.15 },
    { t: "notes", title: "eating types lol", date: "Sunday 9:14 AM", lines: ["🍿 the grazer", "no real meals, just nibbles all day", "", "😮‍💨 the stress eater", "bad text = snack cupboard", "", "🌙 the night nibbler", "\"good\" all day then 9pm happens", "", "🥂 the weekend rebounder", "perfect mon-fri, then brunch + margs"] },
    { t: "vault", sel: "#quiz", text: "i made a lil quiz for it in my guide and it tells u what to fix first" },
  ],
  caption: "comment ur type 👇 im a recovering night nibbler 🌙",
  hashtags: "#whichoneareyou #relatable #weightlosstips #eatinghabits",
  pin: "grazer, stress eater, night nibbler or weekend rebounder? 👇",
},
{
  id: "d7-2-video-demo-quiz", day: 7, time: "12:15 PM", format: "video",
  title: "demo: my own quiz exposed me",
  video: { t: "demo", name: "which-type-quiz" },
  caption: "not me making a quiz and getting exposed by it 💀 which one are u",
  hashtags: "#whichoneareyou #eatingtype #relatable #weightlosstips",
  pin: "quiz is in my bio. tell me ur type 👇",
},
{
  id: "d7-3-carousel-made-a-guide", day: 7, time: "8:00 PM", format: "carousel",
  title: "i put everything in one place",
  slides: [
    { t: "say", img: "rant_car5", text: "i put every tip that actually worked for me in one place and im kinda proud of it ngl", y: 0.14 },
    { t: "vault", sel: "#contents", text: "12 sections, 120 little things. u can tap to jump anywhere" },
    { t: "vault", sel: "#hack-1", text: "each one says why it works + exactly what to do (and roasts u a lil 💀)" },
    { t: "vault", sel: "#bonus-challenge", text: "theres a 30 day thing too if u like ticking boxes like me" },
  ],
  caption: "no starving, no detox tea, no weird pills. just the stuff that actually worked for me 🥹",
  hashtags: "#selfimprovement #weightlossguide #healthyhabits #smallbusiness",
  pin: "its in my bio if u want it. questions? ask me here 👇",
},
];
