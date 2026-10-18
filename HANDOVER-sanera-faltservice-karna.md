# Överlämning — sanera-faltservice-karna

Moduländringarna är gjorda i `/usr/share/odoo-field-service` (gruppskrivbar).
Det som återstår kräver **privilegierad körning** (root/odoo) och en databas.

## 1. Förutsättning: cron_tick

Två moduler har fått ny dependency `cron_tick` (`/usr/share/odoo-base/cron_tick`).
Den måste vara installerad i måldatabasen innan uppgraderingen, annars fallerar
`checkmodule` med "module not found".

```bash
# kontrollera först
sudo -u odoo psql -d <db> -tAc \
  "select name,state from ir_module_module where name in ('cron_tick','fieldservice_sla','l10n_se_resource_calendar_leaves_import')"

# installera vid behov
sudo checkmodule -d <db> -m cron_tick
```

## 2. Uppgradera de sex modulerna

```bash
sudo checkmodule -d <db> -u fieldservice_vrtl
sudo checkmodule -d <db> -u fieldservice_hr
sudo checkmodule -d <db> -u fieldservice_sla
sudo checkmodule -d <db> -u fieldservice_vrtl_ai
sudo checkmodule -d <db> -u ics_import_holidays
sudo checkmodule -d <db> -u l10n_se_resource_calendar_leaves_import
```

Versioner efter bump: `fieldservice_vrtl` 18.0.1.0.1, `fieldservice_hr`
18.0.1.0.1, `fieldservice_sla` 18.0.1.0.1, `fieldservice_vrtl_ai` 18.0.1.0.4,
`ics_import_holidays` 18.0.1.0.1,
`l10n_se_resource_calendar_leaves_import` 18.0.1.0.1.

## 3. Vad som förväntas i loggen

| Loggrad | Innebörd |
|---|---|
| `cannot be found` för `compute` | FEL — 2.1 slog inte igenom |
| `The method "check_all_slas" does not exist` | FEL — 4.5 slog inte igenom |
| `The method "notify_sla_breach" does not exist` | FEL — 4.7 slog inte igenom |
| `module cron_tick not found` | Brist i steg 1 |

Före/efter-kontroll:

```bash
sudo grep -c "cannot be found" /var/log/odoo/odoo-server.log
```

## 4. Första körningen av de nya cron.task-poster

`sla_check_breach` (hour) och `sla_notify_breach` (hour) skapas av
`fieldservice_sla/data/cron_tasks.xml`. `se_holiday_eves` (month) av
`l10n_se_resource_calendar_leaves_import/data/cron_tasks.xml`.

**Varning:** `breach_notified` defaultar till False, så första körningen
notifierar **varje redan bruten SLA-länk en gång**. Det är avsiktligt (det är
den första notifiering de får) men bör aviseras innan uppgraderingen.

Kontrollera efter ett intervall:

```bash
sudo -u odoo psql -d <db> -c \
  "select technical_name, cadence, last_run, failure_count, left(last_error,80) from cron_task where module in ('fieldservice_sla','l10n_se_resource_calendar_leaves_import') order by technical_name"
```

`failure_count = 0` och `last_error` tom = grönt.

## 5. Statisk grind (kan köras utan databas)

```bash
bash /usr/share/odoo-field-service/scripts/sanity-check.sh
# förväntat: "OK — inga fel." och 0 ir.cron, 3 cron.task
```
