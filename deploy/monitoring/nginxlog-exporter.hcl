# prometheus-nginxlog-exporter — AURA edge (node 1) nginx access-log metrics.
#
# Parses /var/log/nginx/aura_metrics.log (written by `log_format aura_metrics`
# in deploy/nginx/nginx.conf) and exposes nginx_http_* metrics on :9113 for the
# node-4 Prometheus to scrape. The `request_uri` relabel collapses paths into
# the edge's route buckets so Grafana shows load distribution per route.
#
# Validate after editing:  prometheus-nginxlog-exporter -config-file <this> -verify-config

listen {
  port = 9113
  address = "0.0.0.0"
}

namespace "nginx" {
  source = {
    files = ["/var/log/nginx/aura_metrics.log"]
  }

  # MUST match `log_format aura_metrics` in deploy/nginx/nginx.conf byte-for-byte,
  # including the literal `rt=` prefix. $request_time drives the latency
  # histogram; method + status labels are derived automatically.
  format = "$remote_addr - $remote_user [$time_local] \"$request\" $status $body_bytes_sent \"$http_referer\" \"$http_user_agent\" rt=$request_time"

  labels {
    app  = "aura-edge"
    node = "node1"
  }

  histogram_buckets = [.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10]

  # Bucket the request path into edge routes. First match wins; each pattern
  # ends in `.*` so the whole value is replaced (bounds label cardinality).
  # Keep specific routes above the `^.*` catch-all.
  relabel "request_uri" {
    from  = "request"
    split = 2

    match "^/api/chat.*"    { replacement = "/api/chat" }
    match "^/api/speech.*"  { replacement = "/api/speech" }
    match "^/api/auth.*"    { replacement = "/api/auth" }
    match "^/api/ecampus.*" { replacement = "/api/ecampus" }
    match "^/backend.*"     { replacement = "/backend" }
    match "^/api.*"         { replacement = "/api-other" }
    match "^/_next.*"       { replacement = "/_next-static" }
    match "^.*"             { replacement = "/frontend" }
  }
}
