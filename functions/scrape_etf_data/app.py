import json
import os
import pickle
import re
import time
from typing import Dict

import boto3
import requests
from bs4 import BeautifulSoup

s3_client = boto3.client("s3")

S3_BUCKET_OUTPUT = os.environ.get('INTERMEDIATE_BUCKET')
S3_FOLDER_OUTPUT = os.environ.get('FOLDER_OUT')

def lambda_handler(event, context):

    # extract ETF isin from event
    isin = event['Records'][0]['body']

    # download response
    time.sleep(1)
    response = download_justetf_webpage(isin, 
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36 Edg/101.0.4951.54",
            "accept-language": "en-GB,en;q=0.9,en-US;q=0.8"
        }
    )

    # raise error if issue
    response.raise_for_status()

    # extract required data from HTML response
    data = scrape_key_data_from_justetf_response(response)

    # save the results to S3 bucket (as a pickle file)
    s3_client.put_object(Bucket=S3_BUCKET_OUTPUT, Key=f"{S3_FOLDER_OUTPUT}{isin}.pkl", Body=pickle.dumps(data))

    return {
        "body": json.dumps(
            {
                "message": f"{isin}",
            }
        ),
    }


def download_justetf_webpage(isin: str, headers: Dict) -> requests.Response:
    '''
    Downloads single JustETF ETF summary page, and returns Requests response object.
    Error checking and logging excluded within this function.
    '''
    response = requests.get(
        url=f'https://www.justetf.com/uk/etf-profile.html?isin={isin}', 
        headers=headers
    )
    return response


def _extract_quote_data(soup: BeautifulSoup) -> tuple:
    '''Extract latest quote and currency from JustETF parsed response'''
    quote_currency, latest_quote = (
        soup.find("div", text=re.compile(r"Quote")).parent.find(class_="val")
        .text.replace('\n', ' ').strip().split()
    )
    return quote_currency, latest_quote


def _extract_latest_quote_date(soup: BeautifulSoup) -> str:
    '''Extract date of latest quote from JustETF parsed response'''
    date_latest_quote = (
        soup.find("div", text=re.compile(r"Quote")).parent.find(class_="vallabel")
        .text.replace('\n', ' ').strip().split()[-1]
    )
    return date_latest_quote


def _extract_dividend_data(soup: BeautifulSoup) -> tuple:
    '''
    Extracts previous 12 month dividend and currency from JustETF parsed response..
    If ETF has no dividends, sets variables to None.
    '''
    try:
        dividend_currency, one_year_dividend = (
            soup.body.find('td', text=re.compile(r'Dividends \(last 12 months\)')).parent.find(class_ = 'val2')
            .text.split(None)
        )
    except Exception:
        dividend_currency = None
        one_year_dividend = None
    return dividend_currency, one_year_dividend


def _extract_expense_ratio(soup: BeautifulSoup) -> tuple:
    '''Extract expense ratio and frequency from JustETF parsed response'''
    expense_ratio, expense_ratio_frequency = (
        soup.body.find('div', text=re.compile('Total expense ratio')).parent.find(class_ = 'val')
        .text.split(None)
    )
    return expense_ratio, expense_ratio_frequency


def scrape_key_data_from_justetf_response(response: requests.Response) -> Dict:
    '''Extracts only required data from a single JustETF response'''

    soup = BeautifulSoup(response.text, 'html5lib')
    
    quote_currency, latest_quote = _extract_quote_data(soup)
    date_latest_quote = _extract_latest_quote_date(soup)
    dividend_currency, one_year_dividend = _extract_dividend_data(soup)
    expense_ratio, expense_ratio_frequency = _extract_expense_ratio(soup)
    
    return {
        'quote_currency': quote_currency,
        'latest_quote': latest_quote,
        'date_latest_quote': date_latest_quote,
        'dividend_currency': dividend_currency,
        'one_year_dividend': one_year_dividend,
        'expense_ratio': expense_ratio,
        'expense_ratio_frequency': expense_ratio_frequency
    }
