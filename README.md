# vannpumpe overvåkning

Overvåkningen består av en NodeMcu microcontroller.

Mikrokontrolleren er er koblet til tre temperatursensorer:
  * i kummen
  * ned i vannet i kummen
  * på baksiden av garasjen

Mikrokontrolleren er også koblet til en infrarød avstandsmåler som måler
avstanden ned til vannspeilet i kummen.


Mikrokontrolleren poster måledataene til https://robots.knutj.org/vannpumpelogserver/log med
jevne mellomrom (per nå ca hvert 90 sekund).

Mikrokontrolleren "autentiserer" seg ved å sende med sin chipid (ESP.getChipId()). Dette er ikke spesielt
sikkert, men så er jo ikke dette en nettbank heller.

Vannpumpelogserveren er en python prosess (kildekoden ligger i "./server"
folderen) som poster måledataene videre til "vannpumpe" indexen i
en Elasticsearch instans.

Pumpedetektoren er en python prosess (kildekoden ligger i "./pumpdetector") som leser
rå-dataene fra elasticsearch og finner ut om pumpen har kjørt. Når en
pumpe-kjøring blir detektert poster denne prosessen en ny entry til
"pumprun" indexen i Elasticsearch instansen. Detekteringen gjøres ved
å se etter plutselige dropp i vannivået.

En Grafana instans på https://robots.knutj.org/grafana brukes til å
visualisere måledataene. Det er lagt til alerts in Grafana som sender
emails dersom vannnivået blir for høyt, eller temperaturen i kummen
blir for lav.

TODO:
Ta backup av elasticsearch og grafana konfigurasjonen.
Sett opp automatisk backup av elasticsearch dataene (offsite backup)

