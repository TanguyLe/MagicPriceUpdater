# MagicPriceUpdate

## CLI help message

```
MagicPriceUpdate: mpu

Usage:
  mpu getstock <current-price-strat> <price-update-strat> [--market-extract-path=<mep>, --output-path=<op>]
  mpu update [--stock-file-path=<sfp>]
  mpu stats [--output-path=<op>]
  mpu (-h | --help)
  mpu --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --market-extract-path=<mep>  Market extract folder path [default: current-directory].
  --output-path=<op> Output folder path [default: current-directory].
  --stock-file-path=<sfp> Input stock file path [default: current-directory/stock.csv].
```

## Behavior

1. `getstock`: Command that performs the following actions :
    1. Gets the current stock from CardMarket.
    2. For each product will try to use a market
    extract file named `<product_id>.json` in the `<mep>`.
    3. If not found, will request the Card Market API to get the market extract and save it as
    `<product_id>.json`.
    4. For each product, will compute the current price using the
    market extract and the `<current-price-strat>`. It will create a new column named
    `"SuggestedPrice"`.
    5. `<price-update-strat>` will be used to eventually add other columns at the
    strategy's discretion.
    6. Creation of the boolean `"PriceApproval"` column by default at `1`, at `0` only
    if the comment contains the special marker `"<manualPrice>"`.
    7. The dataframe will be sorted by `"PriceApproval"` (increasing) and then relative
    difference between the `"Price"` (ref) and the `"SuggestedPrice"`.
    8. Save of the file as csv at `<op>/stock.csv`.
2. Manual edition of the `"PriceApproval"` and `"SuggestedPrice"` columns of the stock file.
3. `update`: Command that performs the following actions :
    1. Read of the csv file `<sfp>`.
    2. Update on Card Market all the prices that have a 1 in `"PriceApproval"` using `"SuggestedPrice"`.
    3. Update on Card Market of the comments of all the other products by adding a 
    marker `"<manualPrice>"` at the end if not already present.
    4. Save of a new file will only those not-updated cards at the same path than `<sfp>`
    but named `notUpdatedStock-<datetime>.csv`.
4. `stats`: Command unrelated to the workflow that generates a file at `<op>/stockStats-<datetime>.csv`,
    With the following information:
    - % of foil/not foil
    - number of cards
    - average card price
    - stock total value
    - number of cards > 5€
    - number of cards < 0.30 €

## Notes
- `<current-price-strat>` and `<price-update-strat>` possible values 
depend on the implemented strategies
- The stats command may easily evolve a lot to compute various indicators
