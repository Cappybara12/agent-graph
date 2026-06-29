# I gave a local AI a memory of my codebase — here's what actually happened

I came across an open-source project called `codebase-memory-mcp` while scrolling through GitHub one evening, and it stopped me. The idea behind it is almost stupidly simple: take your entire codebase and turn it into a graph — every function, every file, every connection between them — so that an AI working on your code can actually look things up instead of quietly guessing and hoping it's right.

I'd hit that exact problem days earlier on a real project of mine. I was about to rename a function and had that small, familiar pause every developer knows — wait, what else in this codebase actually calls this thing? So rather than just trusting whatever an AI tool told me, I spent a weekend testing it properly. Not a thought experiment, not a "this could work" post — I actually ran it against my own code, watched what it got right, and watched it get one thing flat-out wrong too. This is that story.

[GRAPH SCREENSHOT — full 3D graph view, rotating]

This is what my actual codebase looks like once it's been turned into a graph. Every dot here is a real function, file, or component from my project — not a mockup, not a sample repo. The tool doing this, `codebase-memory-mcp`, doesn't have any AI inside it at all, and that's honestly the part I found most interesting once I understood it. It parses your code the same way real editors do under the hood, using tree-sitter, and builds a structural map of your project — pure analysis, zero guessing, zero API key required. The AI only enters the picture once you connect an agent to query that map. In my case, that agent was a small model called qwen2.5, running entirely on my own laptop through Ollama, no internet connection involved.

So here's what I actually wanted to know going in: does handing an AI real facts about a codebase actually change its answers, or is that just a nice story people tell? I set up a fair test to find out — the same model, given the exact same task, run twice. The first time, blind: it only sees the one file where a function is defined, nothing else. The second time, grounded: it's handed the real list of callers straight from the graph before it answers. The function I picked was a real callback in my code called `onStateChange`, which genuinely gets called from four different places in one file, `lib/ws-machine.ts` — I'd already confirmed that with the graph itself before running the test, so I knew exactly what the correct answer looked like.

[TERMINAL SCREENSHOT — terminal_blind_vs_grounded]

The blind agent's answer was short and, frankly, wrong in the way I expected: it pointed only at the file where the function is defined and stopped there, completely missing the file with all four real usages — which makes sense, because it had no way of knowing that file existed. The grounded agent, given the real caller list first, named all four functions correctly and even pointed out that the definition file itself needed a small update too. Same brain, same weights, same everything — the only thing that changed between those two runs was whether it had real facts in front of it before answering. That gap is, as far as I'm concerned, the entire reason this is worth writing about.

That comparison was useful, but it still involved me handing the model its facts on a plate. What I actually wanted to see was whether it would go looking for those facts on its own, without being told to. So I built a second version of the test where the model gets a task and exactly one tool it's allowed to use, if it decides it needs to — a function that queries the real graph for the callers of whatever it's asked about. I gave it this instruction: change the signature of a function called `highlightTarget`, but find out exactly who calls it first, don't guess. And then I just let it run.

[TERMINAL SCREENSHOT — terminal_live_agent_decision]

What you're looking at there is the model deciding, entirely on its own, to call that tool before answering anything. Nobody forced it — it read "don't guess" and acted on it. The query that follows isn't the AI talking, that's the script genuinely hitting the real knowledge graph of my project and getting back two real results. And the final answer it gives is built only from what it just checked, not from a confident-sounding guess.

I didn't want to just take the AI's word for any of this, so right after that run I did the most boring possible verification step: a plain grep, with no AI anywhere near it.

[TERMINAL SCREENSHOT — terminal_grep_verification]

Same two files, same call sites, found the old-fashioned way. The model wasn't making anything up.

Once I'd seen it get things right, I got curious about where it would get things wrong, so I pushed it further and asked the graph to find dead code — functions sitting in the project that nothing calls anymore.

[TERMINAL SCREENSHOT — terminal_dead_code_false_positive]

And this is the part of the weekend I think is actually more valuable than the success stories. Almost everything on that list is wrong. Components like `ToolCallCard` are rendered constantly as JSX elements, and functions like `handleClick` are wired up as event handlers passed through props — the graph's idea of "called" is a direct function-to-function call, and it simply doesn't understand JSX rendering or prop-passing as usage. So it confidently reported a bunch of actively-used code as dead. That's a real limitation, not a knock against the tool, just something worth knowing before you trust any single output from it without checking — which, again, is the whole theme of this experiment.

[GRAPH SCREENSHOT — search/zoom into a specific node]

On a lighter note, one of the more genuinely useful things I tried was just asking for a full summary of my codebase's architecture in a single call, instead of clicking through dozens of files myself to understand how everything's laid out.

[TERMINAL SCREENSHOT — terminal_architecture_overview]

Two hundred and fifty-four nodes, four hundred and sixty-nine edges, a clean breakdown of every language and structure in the project, all from one command. Small thing, but it's the kind of small thing that actually saves real time.

So, stepping back — was having an AI model in the loop at all actually worth it, or could I have just used the graph tool by itself and skipped the AI entirely? I think the honest answer is yes, it was worth it, but for a narrower reason than I expected going in. The graph by itself is genuinely dumb infrastructure — to get anything useful out of it, you need to already know its exact query syntax and parameter names. Without an AI translating for you, you're the one converting a plain-English question like "who calls this function" into a structured query by hand, every single time. What the model actually added wasn't intelligence about my code specifically — it was acting as a natural-language front end to real, ground-truth data, and crucially, knowing on its own when it didn't know something and needed to go check. The mistakes I ran into weren't really the model's fault either — they were the underlying tool's blind spots around JSX and React patterns, which I still had to catch myself by actually reading the output instead of trusting it outright.

If there's one thing I'd want someone to take from this, it's that an AI which checks before it speaks is a fundamentally different, more trustworthy kind of tool than one that just sounds confident — and that difference is something you can actually build and test yourself, on your own laptop, with nothing more than an open-source graph tool and a small local model. That's a modest claim compared to a lot of what gets posted about AI coding tools these days, but it's one I can fully stand behind, because I watched it happen, end to end, on my own real code.

The tool I used throughout this is `codebase-memory-mcp`, built by DeusData — open source, link below. The model was qwen2.5, running locally through Ollama. Every piece of output in this post is real, copy-pasted from my own terminal, including the part where it was wrong.
