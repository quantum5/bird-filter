# Quantum's `bird` Filter Library

This is meant to be a starter repository containing sample `bird` 2.x config
files that you can use to build your own BGP filters. Filters are provided as
composable `bird` functions and enables you to harness the full power of the
`bird` filter mini-programming language, as an alternative to a more declarative
solution like [PathVector][pv].

## Quick start

1. Make sure `bird` 2.x is installed, e.g. on Debian or Ubuntu, through
   `sudo apt install bird2`.
2. Clone this repository:
   ```
   git clone https://github.com/quantum5/bird-filter.git
   cd bird-filter
   ```
3. Customize [`filter_bgp.conf`][filter] by editing it. Pay special attention
   to anything tagged `FIXME`.
4. Install `filter_bgp.conf` into your `bird` configuration directory
   (`/etc/bird` by default):
   ```
   sudo cp filter_bgp.conf /etc/bird
   ```

## Defining BGP sessions

You can use [`skeleton.conf`][skeleton] as a basic `bird` starting config. Note
that in this config, static protocol routes are internal to `bird` and will not
be exported to the kernel routing table. You can change this by changing the
export rules for `protocol kernel`.

This filter library makes use of two basic static protocols:
* `node_v4`: IPv4 routes to be exported by the `export_cone` helper.
* `node_v6`: IPv6 routes to be exported by the `export_cone` helper.

For example, to advertise `198.51.100.0/24` and `2001:db8:1000::/36`:

```
protocol static node_v4 {
    ipv4 {};
    route 198.51.100.0/24 reject;
}

protocol static node_v6 {
    ipv6 {};
    route 2001:db8:1000::/36 reject;
}
```

Two additional static protocols are used to aid with traffic engineering for
anycast prefixes:
* `node_v4_anycast`: IPv4 routes to be exported by the `export_anycast` helper.
* `node_v6_anycast`: IPv6 routes to be exported by the `export_anycast` helper.

You can add `protocol` blocks to this config for each BGP neighbour. This is
dependent on the neighbour type.

In the follow examples, we assume the following local preferences:
* 50 for upstreams;
* 90 for IXPs;
* 100 for direct peers; and
* 120 for downstreams.

### Upstreams

```
protocol bgp example_upstream_v4 {
    description "Example Upstream (IPv4)";
    local 192.0.2.25 as 64500;
    neighbor 192.0.2.24 as 64501;
    default bgp_local_pref 50;

    ipv4 {
        import keep filtered;
        import where import_transit(64501, false);
        export where export_cone(64501);
    };
}

protocol bgp example_upstream_v6 {
    description "Example Upstream (IPv6)";
    local 2001:db8:2000::2 as 64500;
    neighbor 2001:db8:2000::1 as 64501;
    default bgp_local_pref 50;

    ipv6 {
        import keep filtered;
        import where import_transit(64501, false);
        export where export_cone(64501);
    };
}
```

The example above assumes you are AS64500 and establishes BGP sessions over
both IPv4 and IPv6 with an upstream AS64501 and exports your entire cone. It
also assumes your upstream is sending you a full table and filters out the
default route. If you expect a default route instead, use
`import where import_transit(64501, true)`.

To export your anycast as well, you can simply do
`export where export_cone(64501) || export_anycast()`.

### Peers

```
protocol bgp example_peer_v4 {
    description "Example Peer (IPv4)";
    local 192.0.2.25 as 64500;
    neighbor 192.0.2.28 as 64502;
    default bgp_local_pref 100;

    ipv4 {
        import keep filtered;
        import where import_peer_trusted(64502);
        export where export_cone(64502);
    };
}

protocol bgp example_peer_v6 {
    description "Example Peer (IPv6)";
    local 2001:db8:2000::2 as 64500;
    neighbor 2001:db8:2000::10 as 64502;
    default bgp_local_pref 100;

    ipv6 {
        import keep filtered;
        import where import_peer_trusted(64502);
        export where export_cone(64502);
    };
}
```

The example above assumes you are AS64500 and establishes BGP sessions over
both IPv4 and IPv6 with a peer AS64502 and exports your entire cone. It assumes
your peer is trusted and doesn't provide any IRR filtering. If you don't trust
your peer, see the [IRR filtering](#irr-filtering) section below.

### IXP route servers

```
protocol bgp example_ixp_v4 {
    description "Example IXP Route Servers (IPv4)";
    local 203.0.113.3 as 64500;
    neighbor 203.0.113.1 as 64503;
    default bgp_local_pref 90;

    ipv4 {
        import keep filtered;
        import where import_ixp_trusted(64503);
        export where export_cone(64503);
    };
}

protocol bgp example_ixp_v6 {
    description "Example IXP Route Servers (IPv6)";
    local 2001:db8:3000::3 as 64500;
    neighbor 2001:db8:3000::1 as 64503;
    default bgp_local_pref 90;

    ipv6 {
        import keep filtered;
        import where import_ixp_trusted(64503);
        export where export_cone(64503);
    };
}
```

The example above assumes you are AS64500 and establishes BGP sessions over
both IPv4 and IPv6 with the IXP route server whose ASN is 64503 and exports
your entire cone. It assumes your IXP is trusted and doesn't provide any IRR
filtering. If you don't trust your IXP, see the [IRR filtering](#irr-filtering)
section below.

### Downstreams

```
protocol bgp example_downstream_v4 {
    description "Example Downstream (IPv4)";
    local 203.0.113.3 as 64500;
    neighbor 203.0.113.7 as 64504;
    default bgp_local_pref 120;

    ipv4 {
        import keep filtered;
        import where import_downstream(64504, IRR_DOWNSTREAM_V4, IRR_DOWNSTREAM_ASN);
        export where export_to_downstream();
    };
}

protocol bgp example_downstream_v6 {
    description "Example Downstream (IPv6)";
    local 2001:db8:3000::3 as 64500;
    neighbor 2001:db8:3000::7 as 64504;
    default bgp_local_pref 120;

    ipv6 {
        import keep filtered;
        import where import_downstream(64504, IRR_DOWNSTREAM_V6, IRR_DOWNSTREAM_ASN);
        export where export_to_downstream();
    };
}
```

The example above assumes you are AS64500 and establishes BGP sessions over
both IPv4 and IPv6 with a downstream whose ASN is 64504 and exports all your
routes. For your protection, downstream imports without IRR is *not* supported.
For details about setting up IRR, see the [IRR filtering](#irr-filtering)
section below.

## BGP communities

The following large informational communities are implemented by default:
* `YOUR_ASN:1:x`: route received from IXP with ID x;
* `YOUR_ASN:2:x`: route received from neighbour with ASN x;
* `YOUR_ASN:3:100`: route received from peer;
* `YOUR_ASN:3:101`: route received from IXP route server;
* `YOUR_ASN:3:102`: route received from upstream; and
* `YOUR_ASN:3:103`: route received from downstream.

The following large control communities are implemented by default and can be
used by downstreams:
* `YOUR_ASN:10:x`: do not export route to ASx;
* `YOUR_ASN:11:x`: prepend `YOUR_ASN` once upon export to ASx;
* `YOUR_ASN:12:x`: prepend `YOUR_ASN` twice upon export to ASx; and
* `YOUR_ASN:12:x`: prepend `YOUR_ASN` thrice upon export to ASx.

## IRR filtering

1. Follow [`irr-filters.example`][irr-conf] and create `/etc/bird/irr-filters`
   for the peers you would like to filter. (To use alternative locations, edit
   [`make-irr-filter`][irr-script] accordingly.)
2. Run `make-irr-filter` to re-generate IRR filters.
3. Add `include "filter_irr.conf";` into your `bird.conf`.
4. Instead of `import_peer_trusted(asn)` or `import_ixp_trusted(ixp_id)`, use
   `import_peer(asn, IRR_PEER_V4, IRR_PEER_ASN)` or
   `import_peer(asn, IRR_PEER_V6, IRR_PEER_ASN)`, and similarly for IXPs.
5. Create a cron job that runs `make-irr-filter` followed by `birdc configure`.
   Daily is a reasonable cadence.

  [pv]: https://pathvector.io/
  [filter]: filter_bgp.conf
  [skeleton]: skeleton.conf
  [irr-conf]: irr-filters.example
  [irr-script]: make-irr-filter
