#!/usr/bin/env python3

import requests
import argparse
import json
import warnings
from os.path import join
import smtplib
import ssl
from collections import namedtuple


SmtpConfig  = namedtuple('SmtpConfig', 'port server email user password')


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('urls', help='file with urls to crawl')
    parser.add_argument('db_dir', help='directory to store chached data')
    parser.add_argument('--emails', help='send an email with changed urls to'
                        'these addresses (separate multiple addresses by commas)')
    parser.add_argument('--smtp-port', default=465, help='port of smtp server',
                        type=int)
    parser.add_argument('--smtp-server', default='smtp.gmail.com',
                        help='smtp server address')
    parser.add_argument('--smtp-password', help='smtp server password')
    parser.add_argument('--smtp-user', help='smtp server user')
    parser.add_argument('--from-email', help='from email address')
    args = parser.parse_args()

    urls = load_urls(args.urls)
    emails = args.emails.split(',') if args.emails else []
    from_email = args.from_email if args.from_email else args.smtp_user
    smtp_config = SmtpConfig(port=args.smtp_port, server=args.smtp_server,
                             email=from_email, user=args.smtp_user,
                             password=args.smtp_password)

    changed = crawl_urls(urls, args.db_dir)
    report = generate_report(changed)
    if emails:
        send_report(report, emails, smtp_config)
    else:
        print(report)


def load_urls(urls_file):
    with open(urls_file, 'r') as urls_in:
        urls = [url.strip() for url in urls_in.readlines()]
    return urls


def crawl_urls(urls, db_dir):
    cache = load_cache(db_dir)
    changed = {}

    for url in urls:
        r_cached = cache.get(url, '')
        r = requests.get(url)
        if r.text != r_cached:
            cache[url] = r.text
            changed[url] = r.text

    write_cache(cache, db_dir)
    return changed


def load_cache(db_dir):
    try:
        with open(join(db_dir, 'flathunter_cache.json'), 'r') as cache_file:
            cache = json.load(cache_file)
    except FileNotFoundError:
        warnings.warn('cache file could not be found. generating new one')
        cache = {}
    return cache


def write_cache(cache, db_dir):
    with open(join(db_dir, 'flathunter_cache.json'), 'w') as cache_file:
        json.dump(cache, cache_file)


def generate_report(changed):
    for url, content in changed.items():
        print('{}\n{}\n\n'.format(url, content))


def send_report(report, emails, smtp_config):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_config.server, smtp_config.port, context) as server:
        server.login(smtp_config.user, smtp_config.password)
        for email in emails:
            server.sendmail(smtp_config.email, email, report)


if __name__ == '__main__':
    main()
