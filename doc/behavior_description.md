# MagicPriceUpdate

## CLI help message

```
MagicPriceUpdate: mpu

Usage:
  mpu getstock <current-price-strat> <price-update-strat> [--market-extract-path|-mep=<mep>, 
    --config-path|cp=<cp> --output-path|op=<op>, 
    --force-download|-f, --parallel-execution|-p, --minimum-price|m=<mpi>]
  mpu update [--stock-file-path|sfp=<sfp> --yes-to-confirmation|-y]
  mpu stats [--stats-file-path|sfp=<sfp>
  mpu (-h | --help)
  mpu --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --force-download|-f Force the re-download of the market extract regardless if it exists already.
  --parallel-execution|-p Whether to force download the stock or not.
  --market-extract-path|-mep=<mep>  Market extract folder path [default: current-directory].
  --minimum-price|m=<mpi> The minimum price of an artical to be included in the the extract [default: 0].
  --config-path|-cp=<cp> Path to the config. It is mandatory.
  --output-path|-op=<op> Output folder path [default: current-directory].
  --stock-file-path|-sfp=<sfp> Input stock file path [default: current-directory/stock.csv].
  --stats-file-path|-sfp=<sfp> Input stats file path [default: current-directory/stockStats.csv].
  --yes-to-confirmation|-y Prevents the user from being asked for confirmation.
```

## Behavior

1. `getstock`: Command that performs the following actions :
    1. Gets the current stock from CardMarket.
    2. For each product will try to use a market
    extract file named `<product_id>.json` in the `<mep>`.
    3. If not found or if `--force-download` was passed, will request the Card Market API to get 
    the market extract and save it as `<product_id>.json`. (Request params depending on the config)
    4. For each product, will compute the current price using the
    market extract and the `<current-price-strat>` with its options defined in the `<sep>`. It will create a new column named
    `"SuggestedPrice"`.
    5. Creation of the boolean `"PriceApproval"` column by default at `1`, at `0` only
    if the comment contains the special marker `"<M>"` or the strategy didn't return a price.
    6. Adding the column `"RelativePriceDiff"` which is `(current_price - suggested_price) / current_price * 100`
    and rounded to two decimals.
    7. The table will be then sorted by `"PriceApproval"` (increasing) and then
    the absolute value of the `"RelativePriceDiff"` (meaning that `-80%` will be ranked as `80%`).
    8. Adding an empty `"ManualPrice"` column for manual updates.
    9. Save of the file as a styled excel at `<op>/stock.xlsx`.
2. Manual edition of the `"PriceApproval"` (0<->1), `"Comments"` (to eventually 
remove a `"<M>"` marker) and `"ManualPrice"` columns of the stock file.
3. `update`: Command that performs the following actions :
    1. Read of the excel file `<sfp>`.
    2. Update on Card Market all the prices that have a 1 in `"PriceApproval"` using `"SuggestedPrice"`, or articles
    that have something in the `"ManualPrice"` column (obviously this price is used).
    3. Update on Card Market of the comments of all the products updated by a manual price with a  
    marker `"<M>"` at the end if not already present in the comments.
    4. Save of a new file will only the not-updated cards at the same path than `<sfp>`
    but named `notUpdatedStock-<datetime>.xlsx`.
4. `stats`: Command unrelated to the workflow that either appends to an existing file or generates a file a new one,
    the following information:
    - % of foil/not foil
    - number of cards
    - average card price
    - stock total value
    - number of cards > 5€
    - number of cards < 0.30 €

## Notes
- `<current-price-strat>` and `<price-update-strat>` possible values 
depend on the implemented strategies
- The stats command may evolve a lot to compute various indicators
