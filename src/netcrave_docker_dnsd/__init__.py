from netcrave_docker_dnsd.daemon import dns_daemon


if __name__ == '__main__':
    d = dns_daemon()
    asyncio.get_event_loop().run_until_complete(d.main())

