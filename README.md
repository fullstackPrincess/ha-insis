# Инсис Домофон для Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Кастомная интеграция для домофонных систем **Инсис (Профинтел)**, установленных в жилых домах. Позволяет открывать дверь, смотреть камеру и управлять домофоном прямо из Home Assistant.

[English version below](#insis-intercom-for-home-assistant)

## Возможности

- **Замок** — открытие двери из Home Assistant (автоматически закрывается через 5 секунд)
- **Кнопка** — быстрая кнопка "Открыть дверь" для дашбордов и автоматизаций
- **Камера** — живая трансляция RTSP/HLS и снимки JPEG с камеры домофона
- **Несколько дверей** — если у домофона несколько дверей, каждая получает свои сущности
- **Несколько камер** — основная и дополнительная камеры добавляются автоматически
- **Config Flow** — простая настройка через интерфейс с SMS-авторизацией

## Установка

### HACS (рекомендуется)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=fullstackPrincess&repository=ha-insis&category=integration)

Или вручную:

1. Откройте HACS в Home Assistant
2. Нажмите **Интеграции** > **Пользовательские репозитории**
3. Добавьте `https://github.com/fullstackPrincess/ha-insis` как **Интеграция**
4. Найдите **Insis Intercom** и установите
5. Перезапустите Home Assistant

### Вручную

1. Скопируйте папку `custom_components/insis_intercom` в директорию `config/custom_components/` вашего Home Assistant
2. Перезапустите Home Assistant

## Настройка

1. Перейдите в **Настройки** > **Устройства и службы** > **Добавить интеграцию**
2. Найдите **Insis Intercom**
3. Введите номер телефона, привязанный к вашему аккаунту Инсис
4. Введите код из SMS
5. Готово! Устройства домофона появятся автоматически

> **Важно:** Номер телефона должен быть предварительно зарегистрирован в мобильном приложении Инсис.

## Сущности

После настройки для каждого домофона создаются следующие сущности:

| Сущность | Тип | Описание |
|----------|-----|----------|
| Замок | `lock` | Отображается как закрытый; разблокируйте для открытия двери |
| Кнопка открытия | `button` | Нажмите для открытия двери |
| Камера | `camera` | Живая трансляция и снимки |

## Отладка

Для включения отладочных логов добавьте в `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.insis_intercom: debug
```

## Поддерживаемые системы

Интеграция работает с домофонными системами **Инсис / Профинтел** (`dmfn.profintel.ru`). Такие домофоны часто встречаются в новостройках по всей России.

## Отказ от ответственности

Данная интеграция **не связана с компаниями Инсис и Профинтел** и не одобрена ими. Используются неофициальные API, которые могут измениться в любой момент без предупреждения, что может привести к неработоспособности интеграции.

Используйте на свой страх и риск. Авторы не несут ответственности за любые проблемы, возникающие при использовании данной интеграции.

---

# Insis Intercom for Home Assistant

Custom integration for **Insis (Profintel)** intercom systems, commonly installed in Russian apartment buildings. Provides door control, camera streaming, and quick-open buttons directly in Home Assistant.

## Features

- **Lock** — open the door from Home Assistant (auto-relocks after 5 seconds)
- **Button** — quick "Open door" button for dashboards and automations
- **Camera** — live RTSP/HLS stream and JPEG snapshots from your intercom camera
- **Multi-door support** — if your intercom has multiple doors, each gets its own entities
- **Multi-camera support** — primary and secondary cameras are added automatically
- **Config Flow** — easy setup via UI with SMS authentication

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=fullstackPrincess&repository=ha-insis&category=integration)

Or manually:

1. Open HACS in Home Assistant
2. Click **Integrations** > **Custom repositories**
3. Add `https://github.com/fullstackPrincess/ha-insis` as an **Integration**
4. Search for **Insis Intercom** and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/insis_intercom` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **Insis Intercom**
3. Enter your phone number (linked to your Insis account)
4. Enter the SMS code you receive
5. Done! Your intercom devices will appear automatically

> **Note:** The phone number must be registered in the Insis mobile app first.

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| Lock | `lock` | Shows as locked; unlock to open the door |
| Open button | `button` | Press to open the door |
| Camera | `camera` | Live stream and snapshots |

## Disclaimer

This integration is **not affiliated with, endorsed by, or associated with Insis or Profintel** in any way. It uses unofficial APIs that may change at any time without notice, which could break this integration.

Use at your own risk. The authors are not responsible for any issues arising from the use of this integration.

## License

MIT
