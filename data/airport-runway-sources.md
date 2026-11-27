# Airport runway data and modeling notes

Runway bearings and physical dimensions below are from Taiwan CAA eAIP AD 2.12, AIRAC AIP Amendment 05/26 (effective 29 October 2026). Bearings are true bearings. The simulator converts published metres using `M_TO_WORLD = 0.1` (one world unit represents 10 m).

| Simulator code | ICAO | Modeled runway | True bearing | Published length × width |
| --- | --- | --- | ---: | ---: |
| TPE | RCTP | 05L / 23R axis | 049.08° | 3660 × 60 m |
| RMQ | RCMQ | 18 / 36 axis | 176.69° | 3659 × 61 m |
| HUN | RCYU | 03 / 21 axis | 026.32° | 2751 × 45 m |
| MZG | RCQC | 02 / 20 axis | 018.22° | 3000 × 45 m |
| TTT | RCFN | 04 / 22 axis | 038.64° | 2438 × 45 m |
| KHH | RCKH | 09 / 27 axis | 091.90° | 3150 × 60 m |

CAA source pages:

- [RCTP AD 2 — Taoyuan International Airport](https://ais.caa.gov.tw/eaip/AIRAC%20AIP%20AMDT%2005-26_2026_10_29/eAIP/RC-AD%202%20RCTP%20%E8%87%BA%E7%81%A3%E6%A1%83%E5%9C%92%E5%9C%8B%E9%9A%9BTAIPEI-TAIWAN%20TAOYUAN%20INTL-en-GB.html)
- [RCMQ AD 2 — Taichung/Cingcyuangang](https://ais.caa.gov.tw/eaip/AIRAC%20AIP%20AMDT%2005-26_2026_10_29/eAIP/RC-AD%202%20RCMQ%20%E8%87%BA%E4%B8%AD-%E6%B8%85%E6%B3%89%E5%B4%97TAICHUNG-CINGCYUANGANG-en-GB.html)
- [RCYU AD 2 — Hualien](https://ais.caa.gov.tw/eaip/AIRAC%20AIP%20AMDT%2005-26_2026_10_29/eAIP/RC-AD%202%20RCYU%20%E8%8A%B1%E8%93%AEHUALIEN-en-GB.html)
- [RCQC AD 2 — Penghu](https://ais.caa.gov.tw/eaip/AIRAC%20AIP%20AMDT%2005-26_2026_10_29/eAIP/RC-AD%202%20RCQC%20%E6%BE%8E%E6%B9%96PENGHU-zh-TW.html)
- [RCFN AD 2 — Taitung/Fongnian](https://ais.caa.gov.tw/eaip/AIRAC%20AIP%20AMDT%2005-26_2026_10_29/eAIP/RC-AD%202%20RCFN%20%E8%87%BA%E6%9D%B1-%E8%B1%90%E5%B9%B4TAITUNG-FONGNIAN-zh-TW.html)
- [RCKH AD 2 — Kaohsiung International Airport](https://ais.caa.gov.tw/eaip/AIRAC%20AIP%20AMDT%2005-26_2026_10_29/eAIP/RC-AD%202%20RCKH%20%E9%AB%98%E9%9B%84%E5%9C%8B%E9%9A%9BKAOHSIUNG%20INTL-en-GB.html)

## Limits

- The current scene represents one runway axis at each of these six airports. At Taoyuan, the second parallel runway (05R/23L) is not modeled.
- The optional ground-start position is a simplified practice point on the modeled parallel taxi lane, with the engine already at idle; it is not a real gate or pushback procedure. The parallel taxi lane, its two runway connectors, apron surface, terminal, and control tower are simplified gameplay geometry. They are not surveyed taxiway, stand, gate, or building data and must not be treated as airport charts.
- Airport positions and ground elevations are loaded from `data/taiwan-map.json`; this file records its own map/elevation source metadata. The runway table above only documents heading and physical dimensions.
- Aircraft aerodynamic coefficients in `flight-physics.js` are simulator estimates for gameplay, not certified aircraft performance data or flight manuals. The model is point-mass: it does not yet simulate angular inertia, center of gravity, wind, or complete aircraft systems.