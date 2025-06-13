import discord
import sqlite3
import os
import asyncio
import random

from dotenv import load_dotenv

#Set up a database
conn = sqlite3.connect('rpg.db')
c = conn.cursor()

#Create a table of characters
c.execute('''
CREATE TABLE IF NOT EXISTS characters (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    class TEXT,
    level INTEGER,
    xp INTEGER,
    power INTEGER,
    hp INTEGER
)
''')
conn.commit()

try:
    c.execute("ALTER TABLE characters ADD COLUMN hp INTEGER DEFAULT 100")
    conn.commit()
except sqlite3.OperationalError:
    pass

#Create a list of classes and their starting power
class_power = {
    "warrior": 12,
    "mage": 10,
    "tank": 18,
    "peasant": 1
}

#Create hp values for classes
class_hp = {
    "warrior": 30,
    "mage": 25,
    "tank": 35,
    "peasant": 6
}

#Create default weapons for classes
default_equipment = {
    "warrior": {"weapon": "sword"},
    "mage": {"weapon": "grimoire"},
    "tank": {"weapon": "battle axe"},
    "peasant": {"weapon": "stick"}
}

equipment = {} #Stores equipment

active_battles = {} #Stores active battles

class_attacks = {
    "warrior": {
           "slash": {
                 "description": "A sharp sword strike",
                 "damage_range": (12, 16)
              },
            "bash": {
                "description": "A heavy shield bash",
                "damage_range": (8, 12) 
            }
    }, 
    "mage":{
         "fireball": {
             "description": "What else could this possibly be",
             "damage_range": (14, 20)
         },
         "heal": {
             "description": "Aight bruh do you really need me to tell you what this does",
             "healing_range": (10, 15)
         }
    },
    "tank": {
        "slam": {
            "description": "A brutal slam with a battle axe",
            "damage_range": (22, 30)
        },
        "taunt": {
            "description": "Provoke enemies to target you",
            "damage_range": (0, 0)
        }
    },
    "peasant": {
        "poke": {
            "description": "Poke",
            "damage_range": (1, 3)
        },
        "scream": {
            "description": "A cowardly scream",
            "damage_range": (0,0)
        }
        
     }
}
    

    



#Creating a class to interact with the Discord API
class MyClient(discord.Client):
    async def on_ready(self):    #We use an async function to await a successful login
        print('Logged on as {0}'.format(self.user))



#Make sure the bot doesn't reply to itself
    async def on_message(self, message):
        if message.author == self.user:
            return
        

        if message.content.startswith('$hello'):
            await message.channel.send('Hello World!')

            
            
        #Create command to create a character    
        elif message.content.startswith('$create'):
            args = message.content.split()
            if len(args) != 3:
                await message.channel.send("Usage: '$create <name> <class>'")
                return

            name = args[1]
            class_name = args[2].lower()
            hp = class_hp.get(class_name, 100)

            if class_name not in class_power:
                await message.channel.send(f"Invalid Class. Choose from: {', '.join(class_power.keys())}")
                return

            

            #Get the power for the class
            power = class_power[class_name]

            user_id = int(message.author.id)

            

            #Check if character already exists
            c.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
            existing_character = c.fetchone()

            if existing_character:
                #Pull the actual values from the database row
                existing_name = existing_character[1]
                existing_class = existing_character[2]
                level = existing_character[3]
                existing_power = existing_character[5]

                await message.channel.send(
                    f"You already have a name! Welcome Back Traveler!: **{existing_name}** the **{existing_class.capitalize()}** (Level {level}, Power {existing_power})."
                    )
                return

            

            #Insert the new character into the database
            c.execute("INSERT INTO characters (user_id, name, class, level, xp, power, hp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (user_id, name, class_name.capitalize(), 1, 0, power, hp))
            conn.commit()

            await message.channel.send(f"Character Created! Welcome, **{name}** the **{class_name.capitalize()}** (Level 1, Power {power}, HP {hp}).")

            equipment[user_id] = default_equipment[class_name]



        #Creating a list feature to list all adventurers
        elif message.content.startswith('$list'):
            print("List command received!")

            #Fetch all characters from database
            c.execute("SELECT * FROM characters")
            all_characters = c.fetchall()

            #If there are no characters
            if not all_characters:
                await message.channel.send("No characters have been created yet")
                return

            #Build list of characters
            character_list = "\n".join([f"**{char[1]}** the **{char[2]}** (Level {char[3]}, Power {char[5]})" for char in all_characters])

            #Send the list to channel
            await message.channel.send(f"**List of Adventurers:**\n{character_list}")


        #Create a delete character feature
        elif message.content.startswith('$delete'):
            print("Delete command received!")
            user_id = int(message.author.id)

            #Check if the user has a character
            c.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
            existing_character = c.fetchone()


            if existing_character:
                character_name = existing_character[1]
                #Ask for confirmation
                await message.channel.send(f"Are you sure you want to delete your character **{character_name}**? Reply with 'yes' or 'no'.")

                #Wait for confirmation
                def check(m):
                    return m.author == message.author and m.content.lower() in ['yes', 'no']

                try:
                    confirmation_message = await self.wait_for('message', check=check, timeout = 60.0)

                    if confirmation_message.content.lower() == 'yes' :
                        #Delete character
                        c.execute("DELETE FROM characters WHERE user_id = ?", (user_id,))
                        conn.commit()

                        await message.channel.send(f"Your character **{character_name}** has been deleted.")
                    else:
                        await message.channel.send("Character deletion has been canceled.")

                except asyncio.TimeoutError:
                    await message.channel.send("You took too long. Character deletion canceled.")
            else:
                await message.channel.send("You don't have a character.")


        #Command for profile viewer
        elif message.content.startswith('$profile'):
            user_id = int(message.author.id)

            #Fetch character from database
            c.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
            character = c.fetchone()

            if not character:
                await message.channel.send("You don't have a character yet! Use $create <name> <class> to start your Adventure!⚔️")
                return
        

            #Extract player data
            name  = character[1]
            class_name = character[2]
            level = character [3]
            xp = character[4]
            hp = character[6]
            power = character[5]

            if level <= 10:
                title = "Rookie"
            elif level <= 20:
                title = "Adventurer"
            elif level <= 30:
                title = "Veteran"
            else:
                title = "Master"

            flavor_text = f"{title} of the {class_name.capitalize()} class."

            #Get abilities
            abilities = class_attacks.get(class_name.lower(),{})
            abilities_text = "\n".join(f"- **{ability_name.capitalize()}**: {details['description']}" for ability_name, details in abilities.items())

            msg = (
                f"🧑**{title} {class_name.capitalize()}: {name} the {class_name.capitalize()}**\n\n"
                f"⭐ **Level:**{level}     ✨ **XP:** {xp} / 1000\n"
                f"❤️ **HP:** {hp}\n"
                f"👊 **Base Power:** {power}\n\n"
                f"🌀 **Abilities:**\n{abilities_text if abilities_text else 'No abilities yet'}\n"
                "\n\n🎒 **Inventory:**\n"
                + "\n".join(f"- {item}" for item in []) +
                f"\n\n*\"{title} of the {class_name.capitalize()}\"*"
            )

            await message.channel.send(msg)


       #Combat Engine
        elif message.content.startswith('$battle'):
            user_id = message.author.id

            #Check for player
            c.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
            character = c.fetchone()

            if not character:
                await message.channel.send('You need to create a character first')
                return

            player_name  = character[1]
            player_class = character[2].lower()
            player_hp = character[6]
            player_power = character[5]

            #Dummy enemy
            dummy = {
                "name": "Training Dummy",
                "hp": 999999,
                "power": 0 
            }

            await message.channel.send(f"⚔️{player_name} engages the **{dummy['name']}**!\nType '$attack' to strike")

            #Store battle state
            active_battles[user_id] = {
                "enemy": dummy,
                "player_hp": player_hp
            }
        
        #Attack function
        elif message.content.startswith('$attack'):
            user_id = message.author.id

            #Check if the player is in a battle
            if user_id not in active_battles:
                await message.channel.send("You're not in a battle right now. Start one by typing '$battle")
                return
            
            args = message.content.split()

            #Get player data
            c.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
            character = c.fetchone()
            player_name  = character[1]
            player_class = character[2].lower()
            player_power = character[5]
            abilities = class_attacks.get(player_class, {})
            battle = active_battles[user_id]
            dummy = battle["enemy"]

            #if only '$attack' is typed
            if len(args) == 1:
                ability_list = "\n".join([f"**{name}** - {details['description']}" for name, details in abilities.items()])
                await message.channel.send(
                    f"🌀 **Available Abilities for {player_class.capitalize()}**:\n{ability_list}\n\n"
                    f"Use an ability by typing: '$attack <name>' (Ex: '$attack slash')"
                )
                return
            
            #Player is trying to use an ability
            ability_name = args[1].lower()

            if ability_name not in abilities:
                await message.channel.send(f"Ability not found, type '$attack' to view list of abilities")
                return
            
            ability = abilities[ability_name]

            #Healing or damage
            if "healing_range" in ability:
                heal = random.randint(*ability["healing_range"])
                battle["player_hp"] += heal
                await message.channel.send(f"💖{player_name} uses **{ability_name}** and heals for **{heal} HP! 💖")
            else:
                damage = random.randint(*ability["damage_range"])
                dummy["hp"] -= damage
                await message.channel.send(f"🗡️{player_name} uses **{ability_name}**: {ability['description']} and deals **{damage}** damage! 🗡️") 
            
            if dummy.get("power", 0) > 0:
                dummy_damage = random.randint(1, dummy["power"])
                battle["player_hp"] -= dummy_damage
                await message.channel.send(f"💥The {dummy['name']} strikes back for **{dummy_damage}** damage! 💥")

                if battle["player_hp"] <= 0 :
                    await message.channel.send(f"{player_name} has been defeated by the {dummy['name']}... Loser...")
                    del active_battles[user_id]
                    return
            

            #Show updated health
            await message.channel.send(f"⚔️**{player_name} HP:** {battle['player_hp']} | **{dummy['name']} HP:** {dummy['hp']}")


                   
            

            
            


#Establish intents to allow the bot to access messages
intents = discord.Intents.default()
intents.message_content = True

#Use the client token to log into the bot
client = MyClient(intents=intents)
load_dotenv()
token = os.getenv('DISCORD_BOT_TOKEN')
client.run(token)



    
