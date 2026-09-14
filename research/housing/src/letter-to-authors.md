# Черновик письма авторам статьи

Отправляет Алексей сам. Адресаты: Franziska Sielker и Selim Banabak, Institute of
Spatial Planning (Forschungsbereich Stadt- und Regionalforschung), TU Wien.
Адреса на странице института TU Wien; в письме к ним не обращаться по имени без
проверки написания.

Повод: данные для страницы взяты из публичного Feature Service ESPON, а не по
запросу к авторам, — поэтому письмо не запрос, а уведомление с просьбой о двух
вещах: подтвердить, что использование сервиса под атрибуцией их устраивает, и,
если можно, прислать итоговую таблицу статьи (доли населения на странице
расходятся с рисунком 3 на несколько пунктов).

**Второе письмо, отдельное — в ESPON EGTC (info@espon.eu).** Правовая заметка
ESPON, пункт (f), обязывает выслать им копию веб-публикации, использующей их
материалы. Текст ниже, после письма авторам. Требования (a)–(c) той же заметки на
странице уже выполнены: двойное цитирование «© ESPON» и «Origin of data: ESPON
EGTC» и дисклеймер про Monitoring Committee стоят под картой, в блоке источников и
в шапке каждого печатного листа. Пункты (d) и (e) нас не связывают: карта нарисована
своя из их таблицы, оформление карт ESPON не используется и логотип не ставится.

---

Subject: Your Journal of Maps affordability data, reused in an interactive page — with attribution

Dear Dr Sielker, dear Dr Banabak,

I am an independent software engineer and I publish interactive research pages at avgrebenkin.com. I have built a page on top of your Journal of Maps paper "Where can you still afford to live?" (doi:10.1080/17445647.2026.2695777):

https://avgrebenkin.com/research/housing/

The page lets a reader replace the average local income with their own net income, term, rate and down payment, and recomputes the affordable square metres for every municipality, region and country, on a NUTS 3 map with search, comparison and rankings. It is free, has no advertising for anything but my own product, and every number on it is credited to you, to the HOUSE4ALL consortium and to ESPON, with the full citation and DOI.

I want to be transparent about where the numbers came from. Your data availability statement says the data is available on reasonable request. Before writing to you I found that the ESPON HOUSE4ALL StoryMap draws its maps from a public feature service on the ESPON GIS server (HOUSE4ALL_data_at_LAU_level), which carries per-LAU incomes, corrected prices and rents, national rates and the two indicators of the paper. I read all 89,601 rows through its public query interface on 14 September 2026 and checked that your formula reproduces sa_m2 and ra_m2 exactly. The page uses that table, and says so in a section called "Where the numbers come from".

Two requests, both easy to say no to:

1. If reusing the service's table in this form is not what you or ESPON intend, please tell me and I will take the page down or change it to whatever you prefer.

2. The population shares I compute from the service (about 41 % under 50 m² to buy, 37 % to rent) are a few points below the 44 % and 39 % in your figure 3. If the final table behind the paper is available for reuse under attribution, I would gladly replace the service snapshot with it and mark the difference clearly. If not, I will keep quoting your figures as yours and mine as mine.

Thank you for the work. The maps are the first thing I have seen that answers the question in the reader's own units.

With best regards,
Aleksei Grebenkin
Batumi, Georgia
aleksey.v.grebenkin@gmail.com · https://avgrebenkin.com

---

## Второе письмо — в ESPON EGTC

Отправляет Алексей сам, на info@espon.eu. Это не просьба, а выполнение пункта (f)
правовой заметки: уведомление о веб-публикации, использующей материалы ESPON.

---

Subject: Notification under your legal notice — web page using ESPON HOUSE4ALL data

Dear ESPON EGTC,

Your legal notice asks that a copy of any web-based report using ESPON material be sent to you. This is that notification.

The page is https://avgrebenkin.com/research/housing/. It is a free interactive page — free to read, with no advertising except a banner for my own product — that lets a reader enter their own net income, mortgage term, rate and down payment and see how many square metres that buys or rents in each European municipality, region and country. The affordability data comes from the public feature service HOUSE4ALL_data_at_LAU_level on gis-server.espon.eu, read on 14 September 2026, and underpins the HOUSE4ALL work of Sielker, Banabak and the project consortium.

On the requirements in the notice:

- The data is cited twofold as "© ESPON" and "Origin of data: ESPON EGTC".
- The disclaimer "The interpretation of ESPON material does not necessarily reflect the opinion of the ESPON Monitoring Committee" appears under the map, in the sources section, and in the header of every printed sheet.
- No ESPON map is reproduced. The maps on the page were drawn for it from the data table, in my own design, and carry neither the ESPON map design nor the ESPON logo. The page says this explicitly so that no reader mistakes them for ESPON maps.

If any of this falls short of what you intend, please tell me and I will correct or remove the page.

With best regards,
Aleksei Grebenkin
Batumi, Georgia
aleksey.v.grebenkin@gmail.com · https://avgrebenkin.com

---

## Третье письмо — в realtor.com (запрос разрешения на цифры площади)

Отправляет Алексей сам. Адрес **взять с контактной страницы realtor.com/research**
(там указан контакт команды экономических исследований) — в черновике адрес не
проставлен намеренно: проверить его я не смог, домен realtor.com заблокирован
политикой окружения, а выдумывать адрес нельзя.

Зачем письмо: в файле `RDC_Inventory_Core_Metrics_County.csv` есть ровно те два
поля, которых нет ни в одном государственном источнике США, —
`median_listing_price_per_square_foot` и `median_square_feet` по FIPS округа. Без
них американский слой не может считать квадратные метры. Файл лежит в открытом
доступе на S3 без ключа, но открытый доступ — не лицензия: FRED, который
перепубликует эти же ряды, помечает их «Copyrighted: Citation Required» и в своих
правилах запрещает «redistribute any third party's proprietary content … for
commercial use without first obtaining express written permission from the data
provider». Страница бесплатная, но несёт баннер моего продукта, и встраивает
производную таблицу в файл — то есть как раз тот случай, для которого нужно
письменное разрешение.

---

Subject: Permission to reuse county-level listing price per square foot in a free research page

Dear realtor.com economic research team,

I am an independent software engineer and I publish free interactive research pages at avgrebenkin.com. I am writing to ask for written permission to reuse two fields from your Real Estate Data Library, and I would rather ask first than assume.

The page compares housing affordability across countries in a single unit: how many square metres of housing a given income can buy or rent. The European half is built on the ESPON HOUSE4ALL dataset, which publishes price per square metre directly. For the United States I have found no public equivalent: federal statistics carry home values, incomes and rents by county, but floor area is not collected at that level. Your county file is the only openly published source I have found with both a price per square foot and a median size per county.

Concretely I would like to use, from RDC_Inventory_Core_Metrics_County.csv, the fields median_listing_price_per_square_foot and median_square_feet, by county FIPS, averaged over a twelve-month window, and to state plainly on the page that these are asking prices from active listings rather than closed sales.

What that use looks like, so there is no ambiguity:

- The page is free to read and carries no advertising except a banner for my own product, so I treat it as commercial for licensing purposes.
- It works offline: the derived per-county values are embedded in the page itself, and a reader can export the visible table as CSV. So this is redistribution of a derived dataset, not just a chart.
- Every figure would be attributed to realtor.com with a link back, in a section that lists every source on the page, and in the table of provenance next to the field it feeds.
- Nothing is resold, and no listing-level data is used — only your published county aggregates.

If that is acceptable, a short reply saying so is all I need, and I will quote it on the page. If it is not, please tell me what would be, or tell me no — I will build the American half without square metres and say why.

With best regards,
Aleksei Grebenkin
Batumi, Georgia
aleksey.v.grebenkin@gmail.com · https://avgrebenkin.com

---

## Четвёртое письмо — в Redfin (тот же запрос, запасной вариант)

Отправляет Алексей сам. Адрес взять с контактной страницы Redfin Data Center —
в черновике он не проставлен по той же причине: подтверждённого адреса у меня нет.

Отправлять имеет смысл только если realtor.com откажет или промолчит: у Redfin
данные лучше (цены сделок, а не запросов), но правовая позиция хуже. Их Terms of
Use от 29 сентября 2025 (§ 2.3.2–2.3.3) дают «limited, personal, non-exclusive,
non-transferable» право «access, view, and use the Services» и прямо запрещают
«reproduce, redistribute, create derivative works based upon, or attempt to
commercially gain from your use … of the Services». Отдельной лицензии на данные у
обновлённого Data Center нет — я проверил и сам центр, и страницу загрузок, и
статью поддержки «Downloading Data»: разрешения цитировать там больше нет нигде.

---

Subject: Permission to reuse Data Center county medians in a free research page

Dear Redfin,

I am an independent software engineer and I publish free interactive research pages at avgrebenkin.com. I am writing to ask for written permission to reuse a small part of your Data Center county data, because I could not find a licence that grants it.

The page compares housing affordability across countries in one unit: how many square metres a given income buys or rents. For the United States the field I need is the median sale price per square foot by county, from county_market_tracker.tsv, averaged over twelve months.

Why I am asking rather than relying on the Data Center being free to download: the redesigned Data Center, its download hub and the support article on downloading data carry no data licence or citation permission, and your site-wide Terms of Use of 29 September 2025 grant a limited, personal licence to access and view the Services and forbid reproducing, redistributing or creating derivative works from them. My use is none of those things by accident:

- The page is free to read but carries a banner for my own product, so I treat it as commercial.
- The derived per-county values are embedded in the page so it works offline, and readers can export the visible table as CSV — that is redistribution of a derived dataset.
- Everything would be attributed to Redfin with a link back, in the sources section and in the provenance table next to the field it feeds.
- Nothing is resold and no listing-level data is touched — only your published county aggregates.

If Redfin is willing to permit that, a short written reply is all I need, and I will quote it on the page. If not, I will leave the American square-metre figures blank and explain on the page that the data exists but is not licensed for this use.

With best regards,
Aleksei Grebenkin
Batumi, Georgia
aleksey.v.grebenkin@gmail.com · https://avgrebenkin.com
