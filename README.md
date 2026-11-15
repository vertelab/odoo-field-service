# odoo-field-service — gren 19.0

> **Denna gren är avsiktligt tom.** Modulerna är INTE portade till Odoo 19.
> Grenen finns så att dev-miljöer (`hansolo19`) kan klona den utan att falla,
> men den påstår ingenting om att koden är portad.

## Baseline

| | |
|---|---|
| Källa | `20.0` |
| Moduler | **13** |
| Grenar i repot | `16.0`, `18.0`, `20.0` |

## Moduler

- `fieldservice_demo_vrtl`
- `fieldservice_hr`
- `fieldservice_hr_vrtl`
- `fieldservice_material_vrtl`
- `fieldservice_sale_vrtl`
- `fieldservice_sla`
- `fieldservice_sla_vrtl`
- `fieldservice_vrtl`
- `fieldservice_vrtl_account`
- `fieldservice_vrtl_account_vrtl`
- `fieldservice_vrtl_ai`
- `ics_import_holidays`
- `l10n_se_resource_calendar_leaves_import`

## Blockerare

**2 externa beroenden saknas** i Odoo 19-kärnan och OCA 19.0:

| Beroende | Behövs av |
|---|---|
| `cron_tick` | `fieldservice_sla_vrtl` |
| `resource_calendar_leaves_import` | `l10n_se_resource_calendar_leaves_import` |

### Prioritering

Ett beroende som blockerar många moduler ger mest nytta att lösa först:

- `cron_tick` — frisläpper **1** modul(er)
- `resource_calendar_leaves_import` — frisläpper **1** modul(er)

## Nästa steg

Portering sker på `*-pfile`-maskin med versionsagnostisk kod
(`.p.py` / `.p.xml`). Se `/skill:odoo-pfiles`.
