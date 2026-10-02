# Context Is the New Code: code for the book

Plain Python 3.10+, standard library only. `tiktoken` is optional.

Run each demo from this folder:

    python ch01/context_engine_v1.py
    cd ch02 && python inspector.py && cd ..
    python ch03_demo.py      # ... through ch15_demo.py

Chapters 4 to 7 and 12 to 14 have a second example each:
`ch04b_demo.py`, `ch05b_demo.py` and so on. They run the same way
and need no model.

To use a real model, copy `.env.example` to `.env` and fill in
MODEL_URL (a chat-completions endpoint), MODEL_NAME and MODEL_KEY.
`.env` is in `.gitignore`, so your key is never committed. Without
it every demo uses a scripted model and prints the same output.

`tools/stub_server.py` is a stand-in endpoint for checking settings.

## Licence

The code in this repository is released under the MIT License
(see `LICENSE`). The text of the book is not covered by it.
