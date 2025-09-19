#!/usr/bin/env python3
"""
Simple web browser using PyQt5 + QtWebEngine.
Run on Windows (64-bit) with Python 3.8+.
Dependencies:
    pip install PyQt5 PyQtWebEngine

This is intentionally minimal: address bar, back/forward, reload, home, and a QWebEngineView.
Not a production browser — QWebEngine (Chromium) provides rendering, but features like
extensions, profile sandboxing, advanced settings, download manager, etc. are omitted.
"""
import sys
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QToolBar, QAction, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView


class SimpleBrowser(QMainWindow):
    def __init__(self, homepage: str = 'https://www.google.com'):
        super().__init__()
        self.setWindowTitle('网页浏览器')
        self.resize(1000, 700)

        # Web view
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        # Toolbar with navigation
        navtb = QToolBar('导航')
        navtb.setIconSize(navtb.iconSize())
        self.addToolBar(navtb)

        back_btn = QAction('后退', self)
        back_btn.setToolTip('后退')
        back_btn.triggered.connect(self.view.back)
        navtb.addAction(back_btn)

        forward_btn = QAction('前进', self)
        forward_btn.setToolTip('前进')
        forward_btn.triggered.connect(self.view.forward)
        navtb.addAction(forward_btn)

        reload_btn = QAction('刷新', self)
        reload_btn.setToolTip('刷新')
        reload_btn.triggered.connect(self.view.reload)
        navtb.addAction(reload_btn)

        home_btn = QAction('主页', self)
        home_btn.setToolTip('主页')
        home_btn.triggered.connect(lambda: self.navigate_to(homepage))
        navtb.addAction(home_btn)

        navtb.addSeparator()

        # URL / search bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.on_url_entered)
        self.urlbar.setClearButtonEnabled(True)
        navtb.addWidget(self.urlbar)

        # Status bar
        self.status = self.statusBar()

        # Signals
        self.view.urlChanged.connect(self.update_urlbar)
        self.view.loadFinished.connect(self.on_load_finished)

        # Load homepage
        self.navigate_to(homepage)

    def navigate_to(self, url_or_search: str):
        url = url_or_search.strip()
        if not url:
            return
        # If user didn't include scheme, try to guess: treat as search if contains spaces or no dot
        if ' ' in url or '.' not in url:
            # Simple search using Google
            q = QUrl('https://www.google.com/search?q=' + QUrl.toPercentEncoding(url).data().decode('ascii'))
        else:
            if not (url.startswith('http://') or url.startswith('https://')):
                url = 'http://' + url
            q = QUrl(url)
        self.view.setUrl(q)

    def on_url_entered(self):
        text = self.urlbar.text()
        self.navigate_to(text)

    def update_urlbar(self, q: QUrl):
        # Update the URL bar without triggering navigation
        self.urlbar.blockSignals(True)
        self.urlbar.setText(q.toString())
        self.urlbar.blockSignals(False)

    def on_load_finished(self, ok: bool):
        if ok:
            self.status.showMessage('Loaded', 2000)
        else:
            self.status.showMessage('Failed to load', 4000)
            QMessageBox.warning(self, 'Load failed', 'Could not load the page.')


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Simple PyQt Browser')

    browser = SimpleBrowser(homepage='https://www.google.com')
    browser.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
