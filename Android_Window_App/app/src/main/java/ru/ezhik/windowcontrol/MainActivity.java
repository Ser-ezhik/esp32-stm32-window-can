package ru.ezhik.windowcontrol;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.content.SharedPreferences;

public class MainActivity extends Activity {
    private static final String DEFAULT_URL = "http://192.168.100.5/mobile";
    private WebView webView;
    private SharedPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("window_control", MODE_PRIVATE);
        showWeb();
    }

    private void showWeb() {
        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                showSettings("Нет связи с ESP32");
            }
        });
        setContentView(webView);
        webView.loadUrl(prefs.getString("url", DEFAULT_URL));
    }

    private void showSettings(String message) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(28, 28, 28, 28);

        TextView title = new TextView(this);
        title.setText(message + "\nАдрес ESP32:");
        title.setTextSize(18);
        root.addView(title);

        EditText url = new EditText(this);
        url.setSingleLine(true);
        url.setText(prefs.getString("url", DEFAULT_URL));
        root.addView(url);

        Button save = new Button(this);
        save.setText("Сохранить и открыть");
        root.addView(save);

        save.setOnClickListener(v -> {
            prefs.edit().putString("url", url.getText().toString().trim()).apply();
            showWeb();
        });

        setContentView(root);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
