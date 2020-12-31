# MagicPriceUpdater

## Intro

MagicPriceUpdate is a project to design a short tool to smartly and automatically
update selling prices on an online marketplace.

## Installation

The project requires a python3.7 environment, then you just need to 
install the `mpu` with `pip install .` from within the project root directory.

## Usage

### Disclaimer
This is meant to work alongside a private project hosting the actual price updating strategies. 
With the current implementation 
(a submodule and path-dependent strategy discovery, plus base classes in the other project), it is quite hard to add new strategies without access to that private repo.

It might be refactored in the future to ease the way to add strategies by a proper plugin 
system with module discovery.
However, if you are interested in using mpu right now, 
feel free to reach out to the owner to get a 
template of the private repo without the private content.

### Cli

Run the `mpu` commands (for instance `mpu getstock`) in a terminal, 
with the env variables `CLIENT_KEY`, 
`CLIENT_SECRET`, `ACCESS_TOKEN` and `ACCESS_SECRET` defined for the 
[Card Market API](https://api.cardmarket.com/ws/documentation/API_Main_Page).
Help commands are available using `-h`.

Detailed behavior is the [doc](./doc/behavior_description.md).
