# MagicPriceUpdater

## Intro

MagicPriceUpdate is a project to design a short tool to smartly and automatically
update selling prices on an online marketplace.

## Installation

The project requires a python3.7 environment, then you just need to 
install the dependencies with `pip install -r requirements.txt`.

## Usage

Run the `main.py`, with the env variables `CLIENT_KEY`, 
`CLIENT_SECRET`, `ACCESS_TOKEN` and `ACCESS_SECRET` defined for the 
[Card Market API](https://api.cardmarket.com/ws/documentation/API_Main_Page).

# Next steps
- speed improvement with async
- improve the strategies (on a private repo)
- develop the update prices part
- define the final expected workflow
- design the final interface (CLI ?)
