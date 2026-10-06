#!/usr/bin/env python3
"""Calculate a production budget from a supplied quote; never generates media."""
import argparse
import json
from decimal import Decimal

def estimate(rate,seconds,retake_percent=0,other_credits=0):
    rate, seconds, retake, other = map(lambda v:Decimal(str(v)), (rate,seconds,retake_percent,other_credits))
    if any(not value.is_finite() or value < 0 for value in [rate,seconds,retake,other]):
        raise ValueError('Budget inputs must be finite, non-negative numbers.')
    base = rate * seconds
    retries = base * retake / 100
    return {'generated_seconds':float(seconds),'credits_per_second':float(rate),'base_credits':float(base),'retake_allowance_credits':float(retries),'other_credits':float(other),'total_credits':float(base+retries+other),'note':'Local arithmetic from supplied inputs; refresh the provider quote before use.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credits-per-second',type=float,required=True)
    parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--retake-percent',type=float,default=0)
    parser.add_argument('--other-credits',type=float,default=0)
    args = parser.parse_args()
    try:
        result = estimate(args.credits_per_second,args.seconds,args.retake_percent,args.other_credits)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result,indent=2))
