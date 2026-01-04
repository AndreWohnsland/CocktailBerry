# Setting Up and Using the Payment Service

!!! info "First Of All"
    Take note that none of this section is required to run the base program.
    This is a way to run your CocktailBerry machines in a more commercial mode.
    If you are not interested in them, just skip this section.

If you want to use CocktailBerry autonomously, while still charging for cocktails, you can use the NFC Payment Service.
This is an optional feature, where you can use CocktailBerry in a more robust way to limit cocktail spending by some criteria.
A "User" entity is a NFC tag, which can have some (non-personal) properties associated with it.
Currently supported criteria are:

- **Alcohol restriction**: Users can be restricted from ordering alcoholic cocktails (child vs adult).
- **Balance**: Each entity can have a balance, which is checked and deducted when ordering cocktails.

A separate payment service needs to be installed and setup to manage the user entities.
There is a dedicated repository and (see below) setup instructions for this service.

## Prerequisites

To use NFC payments with CocktailBerry, you will need the following:

- NFC reader compatible with the list of supported readers, [ACR1252U](https://amzn.to/4irVt6h) is recommended
- Compatible NFC tags (e.g., [MIFARE Classic](https://amzn.to/43ZPcsC) or [in Blue](https://amzn.to/43ZPcsC))
- The [CocktailBerry Payment](https://github.com/AndreWohnsland/CocktailBerry-Payment) Service reachable over network by your CocktailBerry device
- CocktailBerry version 3.0 or higher

!!! danger "Updating from older Versions?"
    If you are updating from an older version of CocktailBerry, you might need to run some additional setup steps.
    It is recommended to backup your current settings and do a clean install over the setup script instead.
    Then use the backup to restore your settings.

If you want to update your existing installation, do the usual update process.
If CocktailBerry cannot start after the update run:

```bash
cd ~/CocktailBerry
bash scripts/setup_usb_nfc.sh
```

After that, CocktailBerry should start normally again.

## Concept

If this feature is enabled, user will need to scan an NFC tag before being able to order a cocktail.
The tag will be read by the NFC reader, and the unique identifier (UID) of the tag will be sent to the CocktailBerry Manager Service.
The Manager Service will then check if the UID is valid and if the user associated with the tag has sufficient balance to order a cocktail.
A Tag ID can be associated with a 18+ or younger than 18 user, allowing to restrict cocktail orders based on age.
If the UID is valid and the user has sufficient balance, the order will be processed.
The Service will take care of deducting the cocktail price from the user's balance.
Also, managing user balances and age restrictions will be handled by the Manager Service.

Overall Process:

```mermaid
sequenceDiagram
    actor c as Customer
    participant cb as CocktailBerry
    participant p as Payment Service
    actor s as Service Worker
    s-->>p: Initializes NFC chip
    c->>+s: Purchase Card/Balance
    s-->>p: Add Balance
    s->>-c: Supplies NFC Chip
    c->>+cb: Order with NFC
    cb->>+p: Request Info
    p->>-cb: Balance, Info
    cb->>c: Spend Cocktail
    cb->>-p: Subtract Balance
```

The service worker initializes the NFC chip and adds balance when the customer purchases a card.
When the customer orders a cocktail using NFC, CocktailBerry requests user information from the Payment Service.
The Payment Service responds with the user's balance and other relevant information.
CocktailBerry processes the order and deducts the cocktail price from the user's balance.

While it can be optional to scan a tag to view allowed cocktails, scanning a tag is mandatory to order a cocktail.
This pre-selection of allowed cocktails can be used to hide alcoholic cocktails for underage users or similar cases.

<figure markdown>
  ![schema](pictures/payment_schema.svg)
  <figcaption>High-level schema of how the service integrates with CocktailBerry</figcaption>
</figure>

The service consists of two main components:

1. **Backend API**:
A RESTful API built with FastAPI, responsible for handling all payment-related operations, user management, and database interactions.
Only one instance of this should be used to have consistent data.
2. **Frontend GUI**:
Management Admin application for owners to create and top up nfc chips/cards.
You can use as many instances as you want.
While you can run it on the same device as the backend, it is recommended to run it on a separate device for better performance and security.

CocktailBerry Machines using the payment option will communicate with the backend API to process payments and manage user balances.
This requires the machines being either on the same network or having access to the backend API over the internet.
User will then pay the cocktails over NFC cards, while service personal can manage the users and top up balances via the GUI separately.

## Setup

If you have experienced CocktailBerry, you know that we try to simplify the setup as much as possible.
We boiled the process down to a few commands, it will still be a little bit more complex than a regular CocktailBerry setup.
While you can run the backend on the same machine as CocktailBerry, or the the Admin payment GUI, it is recommended to run them on separate devices for better performance and security.

The recommended way for a "basic" hardware setup is:

- A Server (Raspberry Pi 4 or similar) running the payment API over docker
- A desktop device + USB NFC reader running the payment GUI, can be Windows
- CocktailBerry machine + USB NFC reader, connected to the payment API over the network

If you want to really keep it minimalistic, you can also run both API and GUI on the same device, e.g. a Raspberry Pi 4.
In this case you would need to ensure that this device is not down or turned off.
Otherwise users will not be able to order cocktails.
More CocktailBerry machines or GUI instances can be added at any time, just point them to the same backend API.

CocktailBerry machines should be set up according to the official documentation, just ensure that the payment option is enabled and the API URL is set correctly.
For your other devices, follow the steps below, we need to distinguish between Windows and Linux based systems.
MacOS might work as well, but is not officially supported.

### Linux preparation

Linux is the most easy way, since most of the things can be done over a script.
Just run:

```bash
wget -O https://github.com/AndreWohnsland/CocktailBerry-Payment/blob/main/scripts/unix_installer.sh
```

Then follow the [services installation](#service-installation) steps below.

### Windows preparation

Windows can be quite restrictive when it comes to executing scripts and similar tasks.
Make sure the user is able to execute PowerShell as well as Python scripts and can install applications.
If you want to use docker on windows, make sure you [install it](https://docs.docker.com/desktop/setup/install/windows-install/) and set it to auto start with windows.

Then just open a PowerShell terminal as Administrator and run the following command to download and execute the installation script:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://github.com/AndreWohnsland/CocktailBerry-Payment/blob/main/scripts/windows_installer.ps1 | iex"
```

<!-- TODO: LINK -->
<!-- Alternatively, there is also a pre-built executable available for the GUI, which you can download from the release page. -->
<!-- You might not be able to set all options tough when using this directly, so even when using this, going over this preparation and service installation steps is recommended. -->

If [uv](https://docs.astral.sh/uv/getting-started/installation) or [git](https://git-scm.com/install/windows) fails to install, you might need to install them manually first.
Then follow the [services installation](#service-installation) steps below.

### Service installation

Make sure you have followed the preparation steps for your OS.
After that you should already be in the CocktailBerry-Payment folder.
You can use:

```bash
uv run -m cocktailberry.setup
```

to start the interactive setup.
You will be prompted for all necessary information and the script will set up everything for you.
You might need to restart your device after the installation is done, depending on the options you selected and your OS.

## Configuration

You can manage the settings like all other settings over the CocktailBerry Interface.
See also the [Configuration documentation](setup.md) for more details.

In general, the options were made so you can tweak them as you needed.
You might experiment with different settings to find the best fit for your use case.

Some important options are:

- **Opt In**: Enable or disable the payment service integration.
- **Auto Logout**: Automatically log out users after a specified time, only enable this if you are sure this time is more than enough for a user to order a cocktail.
- **Logout after Order**: Log out the user after each order, useful if users usually just order one Cocktail and you use the lock screen.
- **Lock Screen**: User needs to scan his NFC to unlock the cocktail selection. Use this if you want to enforce first time scanning to filter/show only possible cocktails.
- **Show not possible cocktails**: Show all cocktails (not possible in another style), even if the user is not allowed to order them. Might be not the best if you use age restrictions, since they will never be able to order them.
