 | Téma | Wireshark szűrő |
| --- | --- |
| HTTP GET kérés | `http.request.method == "GET"` |
| Konkrét HTTP URI | `http.request.uri == "/ggombos/upload/"` |
| DNS forgalom | `dns` |
| Konkrét DNS név lekérdezése | `dns.qry.name == "oktnb147.inf.elte.hu"` |
| TCP SYN csomagok | `tcp.flags.syn == 1` |
| UDP forgalom | `udp` |
| ICMP forgalom (ping, traceroute) | `icmp` |
| Tanrend URI keresése | `http.request.uri contains "tanrend"` |
| Tanrend DNS lekérdezése | `dns.qry.name == "tanrend.elte.hu"` |
| Forgalom adott IP-re | `ip.dst == 157.181.1.225` |
| HTTP/2 GET kérés | `http2.headers.method == "GET"` |
| Tanrend HTTP/2 forgalma | `http2.headers.authority == "tanrend.elte.hu"` |
| Tanrend CSS fájlok | `http2.headers.authority == "tanrend.elte.hu" and http2.headers.path contains ".css"` |
|  `.css` kiterjesztésű fájlok száma | `http2.headers.path contains` ".css" |
| HTTP POST kérések keresése | `http.request.method == "POST"` |
| Sikeres HTTP válaszok – 200 | `http.response.code == 200` |
| Sikertelen HTTP válaszok – 400 felett | `http.response.code >= 400` |
| Weboldalhoz használt port | `tcp.port == 80` `tcp.port == 443` |
| DNS kérések portja | `udp.port == 53` `tcp.port == 53` |
| DHCP kérések | `dhcp` |
| ARP kérések | `arp` |
| Kérések száma egy adott IP-re | `arp.dst.proto_ipv4  == 192.168.1.1` |
| Titkosított TLS kézfogás | kliens: `tls.handshake.type == 1` szerver: `tls.handshake.type == 2` |
| Milyen oldalakat kértek le? HTTP-forgalom: | `http` -> A kért oldalak/erőforrások az `http.host` és `http.request.uri` mezőkben vizsgálhatók. |
| GET kérések: | `http.request.method == "GET"` |
| Milyen böngészőt használtak? | `http.user_agent` |
| POST kéréssel küldött adatok | `http.request.method == "POST"` Ezután az adott csomagnál: Jobb klikk → Follow → HTTP Stream|
| `.png` képek száma | `http.request.uri contains ".png"` |
| `.png` képek száma HTTP/2 esetén: | `http2.headers.path contains ".png"` |
| Újra nem töltött erőforrások – 304 Not Modified | `http.response.code == 304` Ezután a `Host` és `Request URI` mezők alapján meg lehet nézni, mely oldalakhoz/erőforrásokhoz tartoztak. |
|  | `` |
|  | `` |


 

---

 ## 4\. Egyben – „puskázható” szűrőlista

```
http
http.request.method == "GET"
http.request.method == "POST"
http.request.uri == "/ggombos/upload/"
http.request.uri contains "tanrend"
http.request.uri contains ".css"
http.request.uri contains ".png"

dns
dns.qry.name == "oktnb147.inf.elte.hu"
dns.qry.name == "tanrend.elte.hu"

tcp.flags.syn == 1
udp
icmp

ip.dst == 157.181.1.225

http2.headers.method == "GET"
http2.headers.authority == "tanrend.elte.hu"
http2.headers.path contains ".css"
http2.headers.path contains ".png"

http.response.code == 200
http.response.code >= 400
http.response.code == 304

tcp.port == 80
tcp.port == 443
udp.port == 53
tcp.port == 53

dhcp
arp
arp.dst.proto_ipv4 == <IP-cím>

tls.handshake.type
tls.handshake.type == 1
tls.handshake.type == 2

http.user_agent
```

 ### A legfontosabb vizsgára megtanulandó szűrők

 Ha ebből egy **rövid, csak a feladatmegoldásokhoz szükséges 10–15 soros puskát** kellene készíteni, ezek lennének a legfontosabbak:

```
http.request.method == "GET"
http.request.method == "POST"
http.request.uri contains ".css"
http.request.uri contains ".png"

dns
dns.qry.name == "..."
tcp.flags.syn == 1
udp
icmp

http.response.code == 200
http.response.code >= 400
http.response.code == 304

dhcp
arp

udp.port == 53
tcp.port == 80
tcp.port == 443

tls.handshake.type == 1
tls.handshake.type == 2
```