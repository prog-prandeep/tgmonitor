import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    api_id = int(input("Enter API ID: "))
    api_hash = input("Enter API Hash: ").strip()

    async with TelegramClient(
        StringSession(),
        api_id,
        api_hash
    ) as client:
        string_session = client.session.save()
        print("\n✅ Your String Session:\n")
        print(string_session)


if __name__ == "__main__":
    asyncio.run(main())
