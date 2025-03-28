# Quantum's `bird` Filter Library

This is meant to be a starter repository containing sample `bird` 2.x config
files that you can use to build your own BGP filters. Filters are provided as
composable `bird` functions and enables you to harness the full power of the
`bird` filter mini-programming language, as an alternative to a more declarative
solution like [PathVector][pv].

## Quick start

1. Make sure `bird` 2.x is installed, e.g. on Debian or Ubuntu, through
   `sudo apt install bird2`. This library has not been tested on versions
   older than 2.0.13, so you may run into syntax errors on earlier versions.
   In these cases, you'll need to look into backports or PPAs for a newer
   version.
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

You can use [`skeleton.conf`][skeleton] as a basic `bird` starting config.
Remember to read the `NOTE`s and change the things marked `FIXME`.

Also note that in this config, static protocol routes are internal to `bird`
and will not be exported to the kernel routing table. You can change this by
changing the export rules for `protocol kernel`.

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

### Route collectors

```
protocol bgp route_collector {
    description "Example Route Collector";
    local 2001:db8:2000::2 as 64500;
    neighbor 2001:db8:9000::1 as 64505;
    multihop;

    ipv4 {
        add paths on;
        import none;
        export where export_monitoring();
    };

    ipv6 {
        add paths on;
        import none;
        export where export_monitoring();
    };
}
```

The example above assumes you are AS64500 and establishes a multihop BGP
session with your route collector over IPv6, using multiprotocol BGP to export
routes for both IPv4 and IPv6 in a single session, using `add paths` to also
all routes instead of the best routes available.

### iBGP

There is no true convention regarding iBGP usage since it's strictly internal
to an AS, so this filter library will not attempt to make any assumption about
how you might use iBGP. This means that by default, any route received from
iBGP will not be exported by functions like `export_cone` or
`export_to_downstream`. This avoids potential accidents like internal traffic
engineering hijacks from being exported to the Internet and causing a major
incident.

To export an iBGP route to downstreams, set `export_downstream = 1;` in the
import filter when importing the iBGP route.

To export an iBGP route to upstreams, create a new `export_*` function that
returns `true` for the subset of routes you wish to export, such as
`export_ibgp`. Then, you can write your export clause as follows:

```
export where export_cone([PEER_ASN]) || export_ibgp();
```

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
* `YOUR_ASN:13:x`: prepend `YOUR_ASN` thrice upon export to ASx.

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

## PeeringDB prefix limits

1. Follow [`prefix-limits.example`][prefix-conf] and create
   `/etc/bird/prefix-limits` for peers for whom you'd like to enforce a prefix
   limit.
2. Adjust [`make-prefix-limits`][prefix-script] to use your own PeeringDB mirror
   if you risk getting rate limited.
3. Run `make-prefix-limits` to re-generate the prefix limits file.
4. Add `include "prefix_limit.conf";` into your `bird.conf`.
5. You can use constants like `LIMIT_AS200351_V4` or `LIMIT_AS200351_V6` in your
   `bird.conf`, for example:
   ```
   protocol bgp peer_v6 {
       ...

       ipv6 {
           import limit LIMIT_AS23456_V6 action disable;
           ...
       };
   }
   ```
6. Create a cron job that runs `make-prefix-limits` followed by
   `birdc configure`. Daily is a reasonable cadence.

## RPKI ROA filtering

While this filter library implements RPKI Route Origin Authorization (ROA)
filtering, you still need to populate the `rpki4` and `rpki6` routing tables via
an `rpki` protocol in `bird`. Otherwise, all routes will be treated as RPKI
unknown. This can be configured as follows:

```
protocol rpki {
    roa4 { table rpki4; };
    roa6 { table rpki6; };
    transport tcp;
    remote "127.0.0.1" port 9001;
    retry keep 90;
    refresh keep 900;
    expire keep 172800;
}
```

The example above assumes you are running the RTR protocol on `127.0.0.1:9001`.
This may be provided by something like Routinator, `rtrtr`, `gortr`, or
something similar. I recommend using `rtrtr` to pull a JSON feed from someone's
Routinator instance over HTTPS.

## ASPA filtering (experimental)

This filter library also offers an implementation of the [draft ASPA
standard][aspa] for `bird`. To use it, use the [`make-bird-aspa`][aspa-script]
script to generate the `is_aspa_invalid_pair` function on which
`filter_aspa.conf` depends. This requires the JSON output from Routinator (see
[`aspa/example.json`][aspa-example] for an example):

```console
$ ./make-bird-aspa aspa/example.json > aspa_invalids.conf
```

Then, apply the following patch to [`filter_bgp.conf`][filter]:

```diff
diff --git a/filter_bgp.conf b/filter_bgp.conf
index eb85db7..27a2162 100644
--- a/filter_bgp.conf
+++ b/filter_bgp.conf
@@ -107,6 +107,9 @@ define ASN_BOGON = [
     4294967295              # RFC 7300 Last 32 bit ASN
 ];
 
+include "aspa_invalids.conf";
+include "filter_aspa.conf";
+
 function ip_bogon() {
     case net.type {
         NET_IP4: return net ~ IPV4_BOGON;
@@ -208,6 +211,11 @@ function import_peer_trusted(int peer_asn) {
     bgp_large_community.add((MY_ASN, LC_INFO, INFO_PEER));
     bgp_large_community.add((MY_ASN, LC_PEER_ASN, peer_asn));
 
+    if is_aspa_invalid_peer(peer_asn) then {
+        print proto, ": ", net, ": invalid ASPA: ", bgp_path;
+        return false;
+    }
+
     return import_safe(false);
 }
 
@@ -232,6 +240,11 @@ function import_ixp_trusted(int ixp_id) {
     bgp_large_community.add((MY_ASN, LC_INFO, INFO_IXP_RS));
     bgp_large_community.add((MY_ASN, LC_IXP_ID, ixp_id));
 
+    if is_aspa_invalid_peer(bgp_path.first) then {
+        print proto, ": ", net, ": invalid ASPA: ", bgp_path;
+        return false;
+    }
+
     return import_safe(false);
 }
 
@@ -256,6 +269,11 @@ function import_transit(int transit_asn; bool default_route) {
     bgp_large_community.add((MY_ASN, LC_INFO, INFO_TRANSIT));
     bgp_large_community.add((MY_ASN, LC_PEER_ASN, transit_asn));
 
+    if is_aspa_invalid_upstream() then {
+        print proto, ": ", net, ": invalid ASPA: ", bgp_path;
+        return false;
+    }
+
     return import_safe(default_route);
 }
 
@@ -272,6 +290,11 @@ function import_downstream(int downstream_asn; prefix set prefixes; int set as_s
         }
     }
 
+    if is_aspa_invalid_customer() then {
+        print proto, ": ", net, ": invalid ASPA: ", bgp_path;
+        return false;
+    }
+
     # If they don't want to export this to us, then we won't take it at all.
     if (MY_ASN, LC_NO_EXPORT, MY_ASN) ~ bgp_large_community then {
         print proto, ": ", net, ": rejected by no-export to AS", MY_ASN;
```

A [Python implementation][py-aspa-validate] of the validation function is also
available along with [a suite of tests][py-aspa-test]. This helps ensure the
version in the bird filter language is correct.

  [pv]: https://pathvector.io/
  [filter]: filter_bgp.conf
  [skeleton]: skeleton.conf
  [irr-conf]: irr-filters.example
  [irr-script]: make-irr-filter
  [prefix-conf]: prefix-limits.example
  [prefix-script]: make-prefix-limits
  [aspa]: https://datatracker.ietf.org/doc/draft-ietf-sidrops-aspa-verification/
  [aspa-script]: make-bird-aspa
  [aspa-example]: aspa/example.json
  [py-aspa-validate]: aspa/validate.py
  [py-aspa-test]: aspa/test.py
