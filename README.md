HEAD
# MacroSnap

MacroSnap is a Streamlit nutrition chat demo. A student enters their name and WhatsApp number, asks about food or uploads a meal photo, and gets an approximate calorie and macro estimate from Gemini. They can download a text copy or send a conversation summary to WhatsApp through Twilio.

It uses Gemini for text and image understanding and Twilio for WhatsApp messaging. It does not use OpenCV, MediaPipe, or a trained nutrition model.

## Requirements

- Python 3.9 or newer
- A Google AI Studio API key
- A Twilio account with WhatsApp sandbox access
- Basic Python comfort

## 1. Set up the environment

Open a terminal in this folder and create a virtual environment:

```sh
python -m venv .venv
```

Activate it:

```sh
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows cmd.exe
.venv\Scripts\activate.bat
```

If PowerShell blocks activation, run this in that PowerShell window, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Install the packages:

```sh
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure Gemini

Create an API key in [Google AI Studio](https://aistudio.google.com/app/apikey). Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set `GEMINI_API_KEY` to the key. The default model is `gemini-3.8-flash`; change `GEMINI_MODEL` if your account uses a different available model.

Never commit `secrets.toml` or share your API key.

## 3. Configure the Twilio WhatsApp sandbox

1. In Twilio Console, open **Try it out > Send a WhatsApp message** (or the WhatsApp Sandbox) and follow its instructions to activate the test sender.
2. From the WhatsApp account you entered in MacroSnap, send the sandbox join code to the sandbox number. Before sending the summary, send any new message to the sandbox so the 24-hour customer-service window is open.
3. Open `.streamlit/secrets.toml` and enter the Account SID, Auth Token, and WhatsApp sandbox sender. Use the Account SID and Auth Token from the same Twilio account as the sandbox. Format the sender as `whatsapp:+<number>`.
4. `TWILIO_CONTENT_SID` is optional. Leave it empty to send the summary as a free-form WhatsApp reply during the 24-hour window. If you have an approved template SID, set it and create the template with `{{1}}` for the student's name and `{{2}}` for the summary.

Twilio's Sandbox is for testing. Free-form messages are allowed only during the 24-hour window after the recipient messages the business. Outside that window, use an approved template. Trial accounts may include a limited number of WhatsApp message units; sending may use trial credits or incur Twilio and Meta fees. Check Twilio's current [WhatsApp pricing](https://www.twilio.com/en-us/whatsapp/pricing?locale=en) before sending.

## 4. Run MacroSnap

```sh
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`). Open it in a browser, enter your name and WhatsApp number, then start a chat. Attach a JPG, PNG, or WEBP meal photo if you want a visual estimate. Use **Send conversation summary to WhatsApp** to send the summary, or **Download conversation summary** to save a text copy.

## Project files

```text
macrosnap/
├── app.py
├── prompts.py
├── requirements.txt
├── .gitignore
├── README.md
└── .streamlit/
    └── secrets.toml.example
```

## Notes

- Meal calories and macros are estimates. Photos cannot reveal exact weights, cooking oils, or hidden ingredients.
- Do not use this demo for diagnosis or medical nutrition care.
- The chat state is held in the Streamlit session and is not saved to a database. The user-triggered WhatsApp summary contains chat content, so use only test data in a workshop.
- Gemini usage may be subject to Google AI Studio quotas or pricing for your account.
- A production deployment needs a privacy review, secure secret storage, rate limiting, and a review of the applicable Google, Twilio, and WhatsApp terms.

## Troubleshooting

- **Gemini authentication error:** check `GEMINI_API_KEY`, then restart Streamlit.
- **Model not found or unavailable:** set `GEMINI_MODEL` to a model enabled for your API key.
- **Twilio authentication error:** check that the Account SID and Auth Token are real values from the account that owns the sandbox.
- **Invalid Content SID:** use the template's `HX...` Content SID from that same account.
- **No response after upload:** use a JPG, PNG, or WEBP image smaller than Streamlit's configured upload limit.

# macrosnap
0332916ee5c336f567220c1131dad73d4d6ff41a
