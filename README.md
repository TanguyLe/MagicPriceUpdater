# MagicPriceUpdater

## Intro

MagicPriceUpdate is a project to design a short tool to smartly and automatically
update selling prices on an online marketplace.

## Installation

The project requires a python3.7 environment, then you just need to 
install the `mpu` with `pip install .` from within the project root directory.

## Usage

Run the `mpu` commands (for instance `mpu getstock`) in a terminal, 
with the env variables `CLIENT_KEY`, 
`CLIENT_SECRET`, `ACCESS_TOKEN` and `ACCESS_SECRET` defined for the 
[Card Market API](https://api.cardmarket.com/ws/documentation/API_Main_Page).

# Next steps
- memory improvements on market extracts
- improve the strategies (on a private repo)
- develop the update prices part
- implement the proposed interface
