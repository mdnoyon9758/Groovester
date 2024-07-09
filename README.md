# Groovester

Want a groovy Discord voice channel? Groovester is a Discord Application that can build up a queue of song requests, join Discord voice channels, and play requested song for all to enjoy!

## How to use


### Step 0: Package Setup

This Discord Application relies on Python 3 and several Python modules inorder to operate. 

Assuming you're using Linux Ubuntu, you can install Python 3 using the package manager. If you're operating system is not a flavor or Ubuntu, you will need to look up the command for your specific distribution.

```bash
apt install python3
```

You can install all of the Python modules via the Python package manager.

```bash
pip install --upgrade Discord.py pytube python-dotenv validators
```

### Step 1: Cloning

Clone this repository.

```bash
git clone https://github.com/camsterrrr/Groovester.git
```

### Step 2: Setting Up the Environment

You'll need to create your own Discord application and get your own Discord Application token. There are plenty of guides out there for creating an Application, so I won't go into detail here... 

Before you read any further, ensure that after you've created a Discord application, you add it to your server of choice.

Currently, the Groovester application will pull the application token from a .env file, which is expected to be in the Groovester top-level directory on your local machine. If you locate it anywhere else, you may need to modify the source code. When creating your .env file, format it as follows: `botToken = "your token wrapped in quotes"`.

```
Groovester
|———————— .env
|———————— .git
|———————— src
|			|———————— Groovester.py
|———————— test
|————————README.md
```

### Step 3: Running the Application

Before you read any further, set your working directory as Groovester.

Running the application will take the forground of the terminal. To have the application run in the background, we can use the `screen` command, which allows us to create a session and "tab" in and out of the foreground, sort of like switching between the different tabs in a web browser. Plus, `screen` sessions keep context and history past the lifetime of the terminal's session. 

To create a new `screen` instance run the following command.

```bash
screen -dmS Groovester
screen -S Groovester -X stuff "^M"
screen -S Groovester -X stuff "python3 src/Groovester.py^M"
```

To "reattach" into the `screen` session, issue the following command.

```bash
screen -rS Groovester
```

To detach from the `screen` session, press `ctrl + d`. Don't worry, the application will still be running in the background and any log messages printed will be displayed when you "tab" back into the session.

If you somehow have messed up with the `screen` sessions, you can view and delete individual sessions with the following commands. 

```bash
screen -ls
	There are screens on:
	        18895.Groovester        (07/08/2024 06:06:54 PM)        (Detached)
	        18869.Groovester        (07/08/2024 06:04:24 PM)        (Attached)
screen -XS 18895.Groovester quit
```

### Step 4: Issuing a command

If you closely followed the steps listed up to this point, you should be okay to start issuing commands for Groovester. 

Let's start with `!help`. From the Discord client, navigate to the sever that you added the Discord application to (Step 2). Once there, go into any text channel and type "!help". 

Groovester should reply with the following message: 

```
!play usage:     !play URL to YouTube URL
    Groovester will download YouTube video and play it in a voice channel!

    ...
```

### Step 5: Troubleshooting

Groovester's source code will log messages to the `Groovester.log` file located withing the Groovester directory. Any debug, info, and error messages will be written there. 

Alternatively, you can view log messages by reattaching to the screen session. See instructions listed in Step 3.

### Step 6: Open-Source!

This is an open-source project after all! If you want to contribute a feature, or fork and create your own Discord application, feel free to!

## Details

### Logging

### Multi-Threaded Features

### Temporary Data

## Contributors

Camsterrrr (Oakley.CameronJ@gmail.com) (PGP)

Special thanks to all of the online resources I used while developing this :). There are too many to list, I extend my appreciation either way.
