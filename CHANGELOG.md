# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.4] - 2021-05-09
- Reducing the number of updates per request to 75

## [0.5.3] - 2021-05-04
- Adding debug in case of an update http error

## [0.5.2] - 2021-03-19
- Several aggregations on the same column

## [0.5.1] - 2021-03-14
- Fixing the log problem on windows

## [0.5.0] - 2021-03-13
- A lot more information on the stats
- Not requesting the signed and altered cards
- Switch to a mandatory config path for strategies' options
- Adding options to change the number of cards requested per language, the default max results 
and the requests split

## [0.4.2] - 2021-01-11
- Wider date column in stats output
- Handling nans in stats df (replacing `''` by `float("nan")` and removing lines with only nans)

## [0.4.1] - 2021-01-09
Only getting foil articles when needed

## [0.4.0] - 2021-01-09
Request only foils for foil cards.

## [0.3.0] - 2020-12-31
First version that can be considered stable. Versioning will be consistent from now on.

## [0.2.0] - 2020-12-14
First version of all the commands.

## [0.1.0] - 2020-12-03
First implementation of getstock.
