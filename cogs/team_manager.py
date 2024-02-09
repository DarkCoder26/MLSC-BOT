from discord import client, Interaction, app_commands, PermissionOverwrite, Color, Member, Forbidden, Button, ButtonStyle, SelectOption, Embed
from discord.utils import get
from discord.ext import commands
from bot import MlscBot
from discord.ui import View, Select, button
from firebase_admin import db
from google.cloud import firestore
from csv import DictReader
import os

# Set the environment variable for the path to your Firebase service account key JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "database-key.json"

# Initialize Firestore client
db = firestore.Client()

class TeamManager(commands.Cog):
    def __init__(self, bot: MlscBot):
        self.bot = bot

    @app_commands.command()
    async def register(self, inter:Interaction, team_name: str):
        guild = inter.guild
        author = inter.user
        team_leader = get(guild.roles, name="Team Leader")

        # Create overwrites with allowed roles
        overwrites = {
            guild.default_role: PermissionOverwrite(connect=False),
            author: PermissionOverwrite(connect=True, manage_channels=True)
        }

        if team_name:
            Team_role_status = False
            for role in author.roles:
                if "Team" in role.name:
                    Team_role_status = True
                    break

            if Team_role_status:
                await inter.response.send_message(f"You are already in {role.name}", ephemeral=True)
                
            else:
                try:
                    sameTeam = False

                    with open('Makeathon.csv', 'r') as csvfile:
                        reader = DictReader(csvfile)
                        csv_ids_set = set(row["Team Name"] for row in reader)

                    for vc in guild.voice_channels:
                        if vc.name == f"{team_name}'s Voice channel":
                            sameTeam = True
                            break

                    if not sameTeam and team_name in csv_ids_set:
                        #Create role for team
                        await guild.create_role(name=f"Team {team_name}", colour=Color.from_rgb(0, 31, 63))
                        print(f"{author.name} Created role 'Team {team_name}'")
                        team_role = get(guild.roles, name=f"Team {team_name}")


                        #Assign team leader and team role to command excuter
                        await author.add_roles(team_role)
                        await author.add_roles(team_leader)

                        overwrites[team_role] = PermissionOverwrite(connect=True)

                        #Create voice channel for team
                        team_voice_channel = await guild.create_voice_channel(name=f"{team_name}'s Voice channel", overwrites=overwrites)
                        print(f"{author.name} created {team_voice_channel.name} channel for team {team_name} .....")
                        await inter.response.send_message(f"{team_name}'s Voice channel Created", ephemeral=True),

                    else:
                        await inter.response.send_message(f"This team name already exist !!", ephemeral=True)

                except Exception as e:
                    print(e)
                    await inter.response.send_message("You don't have permission to create teams.", ephemeral=True)

        else:
            inter.response.send_message("Enter team name", ephemeral=True) 

    @app_commands.command()
    async def join_team_member(self, inter: Interaction, team_name: str, member: Member):
        author = inter.user
        guild = inter.guild
        team_leader = get(guild.roles, name="Team Leader")
        role_to_assign = get(guild.roles, name=f"Team {team_name}")

        button_prompt = ButtonPrompt(team_name=team_name)

        if role_to_assign in author.roles and team_leader in author.roles:
            try:
                await inter.response.send_message(f"Invitation send to {member.mention}", ephemeral=True)
                await member.send(f"Do you want to join team {team_name}.", view=button_prompt)
                await button_prompt.wait()

                #when invite is accepted
                if button_prompt.value == True:
                    Team_role_status = False
                    for role in member.roles:
                        if "Team" in role.name:
                            Team_role_status = True
                            break

                    if Team_role_status == True:
                        await member.send(f"You have already Joined {role.name}")
                        await author.send(f"{member.mention} is already in {role.name}")
                    else:
                        await member.add_roles(role_to_assign)
                        await member.send(f"You have accepted invitation from Team {team_name}.")
                        await author.send(f"{member.mention} have accepted your invitation to {team_name}.")

                #when invite is rejected
                elif button_prompt.value == False:
                    await member.send(f"You have rejected invitation from Team {team_name}.")
                    await author.send(f"{member.mention} have rejected your invitation to {team_name}.")
      
            except Forbidden:
                await inter.response.send_message(f"{author.mention} don't have the permissions to assign roles.", ephemeral=True)

        else:
            await inter.response.send_message(f"{author.mention} can't use teamname of other teams", ephemeral=True)

    @app_commands.command()
    async def find_team(self, inter: Interaction):
        dropdown = TeamDropdown()
        view = DropdownView(dropdown)

        try:
            await inter.response.send_message("Select your interest:", view=view, ephemeral=True)

        except IndexError:
            print("list Index error is happening ....")
  
    @app_commands.command()
    async def find_member(self, inter: Interaction):
        dropdown = MemberDropdown(commands.Bot)
        view = DropdownView(dropdown)

        try:
            await inter.response.send_message("Select your Member dev:", view=view, ephemeral=True)
        
        except IndexError:
            print("list Index error is happening ....")


class ButtonPrompt(View):
    def __init__(self, team_name:str):
        super().__init__(timeout=60)
        self.value = None
        self.team_name = team_name

    #Invitation Accept button
    @button(label="Yes", style=ButtonStyle.success)
    async def yes(self, inter: Interaction, button: Button):
        self.value = True
        button.disabled = True
        await inter.response.defer()
        self.stop()

    #Invitation Rejection button
    @button(label="No", style=ButtonStyle.danger)
    async def no(self, inter:Interaction, button: Button):
        self.value = False
        button.disabled = True
        await inter.response.defer()
        self.stop()

class MemberDropdown(Select):
    def __init__(self, bot: MlscBot):
        self.bot = bot
        options = {
            SelectOption(
                label="App dev", description="description", emoji="📱", value="Appdev"
            ),
            SelectOption(
                label="Frontend (Web Dev)", description="description", emoji="🕸️", value="FrontEndWebdev"
            ),
             SelectOption(
                label="Backend (Web Dev)", description="description", emoji="⚙️", value="BackEndWebdev"
            ),
            SelectOption(
                label="AI/ML", description="description", emoji="🤖", value="ML-AI"
            ),
            SelectOption(
                label="UI/UX Design", description="description", emoji="🖼️", value="Design"
            ),
            SelectOption(
                label="Blockchain", description="description", emoji="⚙️", value="Blockchain"
            ),
            SelectOption(
                label="Web3", description="description", emoji="⚙️", value="Web3"
            ),
            SelectOption(
                label="IoT", description="description", emoji="⚙️", value="IoT"
            ),
        }

        super().__init__(placeholder="Select :", options=options)
    
    async def callback(self, inter: Interaction):
        member_list_embed = Embed(title="Members for available", color=0x00FFB3)
        doc_ref = db.collection("Member").document(self.values[0])
        memberlist = []

        doc = doc_ref.get()
        if doc.exists:
            discord_ids = doc.to_dict()
            for id in discord_ids["Discord_id"]:
                memberlist.append(int(id))
        else:
            print("No such document!")

        def check_role(user_id):
            flag = 0
            try:
                for role in inter.guild.get_member(int(user_id)).roles:
                    if "Team" in role.name:
                        flag = 1
                        break
                return flag
            except Exception as e:
                flag = 2
                print(e)
        
        for member in memberlist:
            if check_role(member) == 0:
                try:
                    member_list_embed.add_field(name=f"{inter.guild.get_member(int(member))}", value="", inline=False)
                except Exception as e:
                    print(e)

        await inter.response.send_message(embed=member_list_embed, ephemeral=True)

class TeamDropdown(Select):
    def __init__(self):
        options = {
            SelectOption(
                label="App dev", description="description", emoji="📱", value="Appdev"
            ),
            SelectOption(
                label="Frontend (Web Dev)", description="description", emoji="🕸️", value="FrontEndWebdev"
            ),
             SelectOption(
                label="Backend (Web Dev)", description="description", emoji="⚙️", value="BackEndWebdev"
            ),
            SelectOption(
                label="AI/ML", description="description", emoji="🤖", value="ML-AI"
            ),
            SelectOption(
                label="UI/UX Design", description="description", emoji="🖼️", value="Design"
            ),
            SelectOption(
                label="Blockchain", description="description", emoji="⚙️", value="Blockchain"
            ),
            SelectOption(
                label="Web3", description="description", emoji="⚙️", value="Web3"
            ),
            SelectOption(
                label="IoT", description="description", emoji="⚙️", value="IoT"
            ),
        }

        super().__init__(placeholder="Select :", options=options)
    
    async def callback(self, inter: Interaction):
        author = inter.user
        member_list_embed = Embed(title="Members for available", color=0x00FFB3)

        doc_ref = db.collection("Member").document(self.values[0])
        memberlist = []

        doc = doc_ref.get()
        if doc.exists:
            discord_ids = doc.to_dict()
            for id in discord_ids["Discord_id"]:
                memberlist.append(id)

        memberlist.append(f"{author.id}") # add user id here
        
        id_ref = db.collection("Member").document(self.values[0])
        data = {"Discord_id": memberlist}
        id_ref.set(data, merge=True)

        await inter.response.send_message(f"You have selected {self.values[0]}", ephemeral=True)

class DropdownView(View):
    def __init__(self, dropdown: Select):
        super().__init__(timeout=60)
        self.add_item(dropdown)

async def setup(bot: commands.Bot):
    await bot.add_cog(TeamManager(bot))