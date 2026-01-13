# Scraping Strategy

## how many different html classes are there?
check class "main_content_wrapper" and within class, get all other classes

ema-node-content-wrapper node-sections

skip ema-embedded-view?

## Parsing of possible Videos links in /eu/events/
E.g. a button  with title "Show external content" -> Then Iframe with e.g. embedded youtube video. Or directly from
data-location="https://webtools.europa.eu/crs/iframe?addconsent=youtube.com&amp;oriurl=https%3A%2F%2Fwww.youtube.com%2Fembed%2Fvideoseries%3Flist%3DPL7K5dNgKnawbgoFUuaWKheqiRBVP3WcBT"

## glossary terms
this very simple layout should be parsed separately
https://www.ema.europa.eu/en/glossary-terms/adjunct

How to deal with parent pages?
https://www.ema.europa.eu/en/about-us/glossaries/glossary-regulatory-terms

## Expand collapsed accordeon
class="accordion-button collapsed"

## Deal with table class (e.g. after exapnding an accordion)


## Very Important!!!
All data is in Json now!!! -> I do not have to deal with extracting meta information from PDFs!!! 
https://www.ema.europa.eu/en/about-us/about-website/download-website-data-json-data-format