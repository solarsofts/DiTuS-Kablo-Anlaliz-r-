"""Ekrana duyarlı pencere yerleşimi için tek otorite.

Pencereler sabit piksel geometrisi veya ``maximumSize`` ile kilitlenmez.  Her
üst düzey DiTuS penceresi ilk gösterimde aktif monitörün *availableGeometry*
alanına göre içerik-duyarlı boyutlandırılır; görev çubuğu/menü çubuğu alanı
hesaba katılır. Kullanıcı daha sonra pencereyi serbestçe yeniden boyutlandırır,
maksimize eder veya başka monitöre taşır.

Bu modül iki katman sağlar:

* :func:`fit_window` — açıkça çağrılan pencere için yoğunluk + içerik sizeHint'i
  ile ilk boyutu çözer.
* :class:`ResponsiveWindowManager` — doğrudan veya yardımcı modül içinden
  açılan bütün üst düzey QDialog/QMainWindow örneklerini ilk Show olayında aynı
  kurala sokar. Böylece tek tek çağrı noktalarının unutulması pencerenin ekran
  dışına kaçmasına yol açmaz.

Önemli tasarım kuralı: ekran boyutu yalnız *ilk yerleşim sınırı*dır, maksimum
boyut değildir. ``setMaximumSize(availableGeometry)`` kullanılmaz; bu, Windows
maksimize düğmesini fiilen etkisizleştiren önceki hataydı.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QRect, QTimer, Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QWidget

__all__ = [
    "DENSITY_COMPACT",
    "DENSITY_NORMAL",
    "DENSITY_WIDE",
    "DENSITY_FULL",
    "DENSITY_FRACTIONS",
    "available_work_area",
    "fit_window",
    "clamp_to_screen",
    "install_responsive_window_manager",
]

DENSITY_COMPACT = "COMPACT"
DENSITY_NORMAL = "NORMAL"
DENSITY_WIDE = "WIDE"
DENSITY_FULL = "FULL"

# Bunlar pencerenin ulaşabileceği *varsayılan* üst oranlardır; kullanıcı
# maksimize ettiğinde uygulanmaz. İçerik daha küçükse sizeHint korunur.
DENSITY_FRACTIONS: dict[str, tuple[float, float]] = {
    DENSITY_COMPACT: (0.62, 0.72),
    DENSITY_NORMAL: (0.80, 0.84),
    DENSITY_WIDE: (0.93, 0.91),
    DENSITY_FULL: (0.97, 0.96),
}

_FLOOR: dict[str, tuple[int, int]] = {
    DENSITY_COMPACT: (460, 360),
    DENSITY_NORMAL: (680, 500),
    DENSITY_WIDE: (860, 580),
    DENSITY_FULL: (960, 640),
}

_MARGIN = 12
_CONTENT_PAD = 24


def _screen_for(widget: QWidget | None):
    screen = None
    if widget is not None:
        try:
            handle = widget.window().windowHandle()
        except RuntimeError:
            handle = None
        if handle is not None:
            screen = handle.screen()
        if screen is None:
            parent = widget.parentWidget()
            if parent is not None:
                screen = parent.screen()
    return screen or QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()


def available_work_area(widget: QWidget | None = None) -> QRect:
    """Aktif monitörün görev çubuğu düşülmüş kullanılabilir alanı."""

    screen = _screen_for(widget)
    if screen is None:
        return QRect(0, 0, 1280, 800)
    return screen.availableGeometry()


def _density_of(widget: QWidget, fallback: str = DENSITY_NORMAL) -> str:
    value = str(widget.property("ditus_window_density") or "").upper()
    return value if value in DENSITY_FRACTIONS else fallback


def _resolve_size(widget: QWidget, density: str, area: QRect) -> tuple[int, int]:
    fraction_w, fraction_h = DENSITY_FRACTIONS.get(density, DENSITY_FRACTIONS[DENSITY_NORMAL])
    usable_w = max(320, area.width() - 2 * _MARGIN)
    usable_h = max(240, area.height() - 2 * _MARGIN)
    cap_w = max(320, int(round(usable_w * fraction_w)))
    cap_h = max(240, int(round(usable_h * fraction_h)))
    floor_w, floor_h = _FLOOR.get(density, _FLOOR[DENSITY_NORMAL])

    # sizeHint, kurucu sonunda gerçek içeriğin doğal boyutunu taşır. İlk
    # fit_window çağrısı kurucunun başındaysa Show-event yöneticisi aynı hesabı
    # içerik tamamlandıktan sonra bir kez daha yapar.
    hint = widget.sizeHint()
    hint_w = max(0, int(hint.width())) + _CONTENT_PAD
    hint_h = max(0, int(hint.height())) + _CONTENT_PAD

    width = min(usable_w, cap_w, max(min(floor_w, usable_w), hint_w))
    height = min(usable_h, cap_h, max(min(floor_h, usable_h), hint_h))
    return max(320, width), max(240, height)


def _enable_user_window_controls(widget: QWidget) -> None:
    """DiTuS çalışma pencerelerinde minimize/maksimizeyi kullanıcıya bırak."""

    if isinstance(widget, QMessageBox):
        return
    flags = widget.windowFlags()
    flags |= Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
    if flags != widget.windowFlags():
        widget.setWindowFlags(flags)


def fit_window(
    widget: QWidget,
    density: str = DENSITY_NORMAL,
    *,
    center_on: QWidget | None = None,
    keep_position: bool = False,
) -> None:
    """Pencerenin *normal* durumdaki ilk geometrisini aktif ekrana sığdır.

    Bu fonksiyon pencereyi hiçbir zaman maksimum boyuta kilitlemez. Kullanıcı
    maksimize/fullscreen yaptıysa durumuna dokunulmaz.
    """

    density = density if density in DENSITY_FRACTIONS else DENSITY_NORMAL
    widget.setProperty("ditus_window_density", density)
    _enable_user_window_controls(widget)

    if widget.isMaximized() or widget.isFullScreen():
        return

    reference = center_on if center_on is not None else widget
    area = available_work_area(reference)
    width, height = _resolve_size(widget, density, area)

    # Önceki sürümden kalan veya bir kurucuda verilmiş üst seviye minimum
    # geometriler ekranın kazanmasını engellemesin. İç widget'ların kendi
    # minimumları değiştirilmez.
    widget.setMinimumSize(0, 0)
    widget.resize(width, height)

    if keep_position and widget.isVisible():
        geometry = widget.frameGeometry()
        x = min(max(geometry.x(), area.x() + _MARGIN), max(area.x() + _MARGIN, area.right() - width - _MARGIN + 1))
        y = min(max(geometry.y(), area.y() + _MARGIN), max(area.y() + _MARGIN, area.bottom() - height - _MARGIN + 1))
    else:
        if center_on is not None and center_on.isVisible():
            anchor = center_on.frameGeometry().center()
            x = anchor.x() - width // 2
            y = anchor.y() - height // 2
        else:
            x = area.x() + (area.width() - width) // 2
            y = area.y() + (area.height() - height) // 2
        x = min(max(x, area.x() + _MARGIN), max(area.x() + _MARGIN, area.right() - width - _MARGIN + 1))
        y = min(max(y, area.y() + _MARGIN), max(area.y() + _MARGIN, area.bottom() - height - _MARGIN + 1))

    widget.move(int(x), int(y))
    widget.setProperty("ditus_initial_fit_done", True)


def clamp_to_screen(widget: QWidget) -> None:
    """Normal durumdaki pencereyi aktif monitörün görünür alanına geri getir."""

    if widget.isMaximized() or widget.isFullScreen():
        return
    area = available_work_area(widget)
    geometry = widget.frameGeometry()
    width = min(max(320, geometry.width()), max(320, area.width() - 2 * _MARGIN))
    height = min(max(240, geometry.height()), max(240, area.height() - 2 * _MARGIN))
    x = min(max(geometry.x(), area.x() + _MARGIN), max(area.x() + _MARGIN, area.right() - width - _MARGIN + 1))
    y = min(max(geometry.y(), area.y() + _MARGIN), max(area.y() + _MARGIN, area.bottom() - height - _MARGIN + 1))
    widget.setMinimumSize(0, 0)
    widget.resize(int(width), int(height))
    widget.move(int(x), int(y))


class ResponsiveWindowManager(QObject):
    """Unutulan yardımcı pencereleri de tek ekran-sığdırma yoluna sokar."""

    def _managed_window(self, obj: object) -> QWidget | None:
        if not isinstance(obj, (QDialog, QMainWindow)):
            return None
        if isinstance(obj, QMessageBox):
            return None
        if not obj.isWindow():
            return None
        if bool(obj.property("ditus_disable_auto_fit")):
            return None
        return obj

    def eventFilter(self, obj: object, event: QEvent) -> bool:  # noqa: N802
        widget = self._managed_window(obj)
        if widget is None:
            return super().eventFilter(obj, event)

        event_type = event.type()
        if event_type == QEvent.Polish:
            _enable_user_window_controls(widget)
        elif event_type == QEvent.Show:
            # Show öncesinde layout henüz son sizeHint'ini vermemiş olabilir;
            # event-loop'a dönünce bir kez sığdır.
            if not bool(widget.property("ditus_initial_fit_done")):
                density = _density_of(widget)
                QTimer.singleShot(0, lambda w=widget, d=density: fit_window(w, d, center_on=w.parentWidget()))
            else:
                QTimer.singleShot(0, lambda w=widget: clamp_to_screen(w))
        elif event_type == QEvent.WindowStateChange:
            # Maximize'dan normale dönünce pencere eski monitör dışında kalmışsa
            # sadece görünür alana çek; kullanıcının seçtiği normal boyutu bozma.
            QTimer.singleShot(0, lambda w=widget: clamp_to_screen(w))
        else:
            screen_change = getattr(QEvent.Type, "ScreenChangeInternal", None)
            if screen_change is not None and event_type == screen_change:
                QTimer.singleShot(0, lambda w=widget: clamp_to_screen(w))
        return super().eventFilter(obj, event)


def install_responsive_window_manager(app: QApplication) -> ResponsiveWindowManager:
    """Uygulama genelinde üst düzey pencere sığdırma yöneticisini kur."""

    manager = ResponsiveWindowManager(app)
    app.installEventFilter(manager)
    # Python GC'nin eventFilter nesnesini toplamaması için uygulamada referans.
    app.setProperty("ditus_responsive_window_manager_installed", True)
    app._ditus_responsive_window_manager = manager  # type: ignore[attr-defined]
    return manager
