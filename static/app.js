if (window.DASH) {
  fetch("/api/dashboard")
    .then(r => r.json())
    .then(d => {
      const $ = id => document.getElementById(id);
      const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

      $("asof").innerHTML = `Data as of <b>${esc(d.asof)}</b> <span class="tag" style="margin-left:6px;">Latest Report Timestamp · Demo Clock</span>`;

      // Render KPIs with colored top bars & modern typography
      const K = [
        { label: "Total Reports", val: d.kpi.total, color: "#0284c7" },
        { label: "SIF Potential", val: d.kpi.sif, color: "#dc2626" },
        { label: "High / Critical", val: d.kpi.high_critical, color: "#ea580c" },
        { label: "Open Actions", val: d.kpi.open_actions, color: "#ca8a04" },
        { label: "Overdue Actions", val: d.kpi.overdue, color: "#e11d48" },
        { label: "Emerging Risks", val: d.kpi.emerging, color: "#7c3aed" }
      ];

      $("kpis").innerHTML = K.map(k => `
        <div class="kpi">
          <div class="kpi-bar" style="background:${k.color}"></div>
          <span style="color:${k.color}">${esc(k.label)}</span>
          <b>${esc(k.val)}</b>
        </div>
      `).join("");

      // Render Emerging Risk Alerts Box
      const alertHtml = d.alerts.length ? d.alerts.map(a => `
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; padding:10px 14px; background:#f8fafc; border-radius:8px; margin-top:8px; border:1px solid #e2e8f0;">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="badge ${a.level}">${esc(a.level)}</span>
            <span style="font-weight:700; color:var(--text-main); font-size:14px;">${esc(a.site)}</span>
            <span class="tag" style="background:#e0f2fe; color:#0369a1; font-weight:700;">${esc(a.hazard)}</span>
          </div>
          <div style="font-size:13px; color:var(--text-muted);">
            7-day window: <b>${esc(a.previous_count)}</b> &rarr; <b style="color:#b91c1c;">${esc(a.current_count)}</b> reports 
            <span class="badge ${a.level}" style="font-size:10px; margin-left:6px;">
              ${a.growth_percent == null ? "NEW SPIKE" : "+" + esc(a.growth_percent) + "% GROWTH"}
            </span>
          </div>
        </div>
      `).join("") : `<p class="muted" style="margin:6px 0;">No active statistical emerging-risk alerts triggered at this time.</p>`;

      $("alertbox").innerHTML = `
        <h4 style="margin-bottom:4px;">
          Active Emerging Risk Alerts
          <span class="tag" style="background:#fef3c7; color:#92400e;">Statistical 7-day Surveillance</span>
        </h4>
        <p class="muted" style="margin-bottom:6px;">Triggers when current 7-day reports &ge; 3 and &ge; 2&times; previous window.</p>
        ${alertHtml}
      `;

      // Render Charts if Chart.js is loaded
      if (typeof Chart !== "undefined") {
        Chart.defaults.font.family = "'Plus Jakarta Sans', system-ui, sans-serif";
        Chart.defaults.color = "#64748b";

        const lineOptions = {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false } },
            y: { grid: { color: "rgba(226, 232, 240, 0.6)" }, beginAtZero: true }
          }
        };

        const barOptions = (horizontal) => ({
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: horizontal ? "y" : "x",
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: "rgba(226, 232, 240, 0.6)" }, beginAtZero: true },
            y: { grid: { display: !horizontal } }
          }
        });

        // 1. Weekly SIF
        new Chart($("c_sif"), {
          type: "line",
          data: {
            labels: d.weekly_sif.map(x => x.week),
            datasets: [{
              label: "SIF Reports",
              data: d.weekly_sif.map(x => x.count),
              borderColor: "#0284c7",
              backgroundColor: "rgba(2, 132, 199, 0.12)",
              fill: true,
              tension: 0.3,
              pointBackgroundColor: "#0284c7",
              pointRadius: 3
            }]
          },
          options: lineOptions
        });

        // 2. Weekly High/Critical
        new Chart($("c_hc"), {
          type: "line",
          data: {
            labels: d.weekly_hc.map(x => x.week),
            datasets: [{
              label: "High/Critical",
              data: d.weekly_hc.map(x => x.count),
              borderColor: "#ea580c",
              backgroundColor: "rgba(234, 88, 12, 0.12)",
              fill: true,
              tension: 0.3,
              pointBackgroundColor: "#ea580c",
              pointRadius: 3
            }]
          },
          options: lineOptions
        });

        // 3. Types Doughnut
        new Chart($("c_types"), {
          type: "doughnut",
          data: {
            labels: Object.keys(d.types),
            datasets: [{
              data: Object.values(d.types),
              backgroundColor: ["#0284c7", "#ea580c", "#10b981", "#6366f1"],
              borderWidth: 2,
              borderColor: "#ffffff"
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "68%",
            plugins: {
              legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } }
            }
          }
        });

        // 4. Site Density
        new Chart($("c_sites"), {
          type: "bar",
          data: {
            labels: d.sites.map(s => `${s.site} (n=${s.total})`),
            datasets: [{
              label: "% SIF-Potential",
              data: d.sites.map(s => s.density_pct),
              backgroundColor: "rgba(2, 132, 199, 0.85)",
              borderRadius: 6
            }]
          },
          options: barOptions(true)
        });

        // 5. Life Saving Rules
        new Chart($("c_rules"), {
          type: "bar",
          data: {
            labels: Object.keys(d.rules).slice(0, 7),
            datasets: [{
              label: "Observations",
              data: Object.values(d.rules).slice(0, 7),
              backgroundColor: "rgba(99, 102, 241, 0.85)",
              borderRadius: 6
            }]
          },
          options: barOptions(true)
        });

        // 6. Barrier Failures
        new Chart($("c_bar"), {
          type: "bar",
          data: {
            labels: Object.keys(d.barriers).slice(0, 7),
            datasets: [{
              label: "Failures",
              data: Object.values(d.barriers).slice(0, 7),
              backgroundColor: "rgba(236, 72, 153, 0.85)",
              borderRadius: 6
            }]
          },
          options: barOptions(true)
        });
      }

      // Render Tables
      const tbl = (rows, cols) => rows.length ? `
        <div class="table-wrap">
          <table>
            <tr>${cols.map(c => `<th>${c[1]}</th>`).join("")}</tr>
            ${rows.map(r => `
              <tr>
                ${cols.map(c => {
                  const val = r[c[0]];
                  if (c[0] === 'risk_level') {
                    return `<td><span class="badge ${val}">${esc(val)}</span></td>`;
                  }
                  if (c[0] === 'text') {
                    return `<td class="report-text" title="${esc(val)}">${esc(String(val).slice(0, 140))}${String(val).length > 140 ? '…' : ''}</td>`;
                  }
                  return `<td>${esc(val)}</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </table>
        </div>
      ` : "<p class='muted' style='margin:4px 0;'>None recorded.</p>";

      const rc = [
        ["id", "ID"],
        ["reported_at", "Date"],
        ["site", "Site"],
        ["severity", "Severity"],
        ["risk_level", "Risk Level"],
        ["risk_score", "Score"],
        ["text", "Observation"]
      ];

      $("repeats").innerHTML = tbl(d.repeats, [
        ["site", "Facility / Site"],
        ["hazard", "Hazard Type"],
        ["count", "Repeat Occurrences (30d)"]
      ]);

      $("hidden").innerHTML = tbl(d.hidden, rc);
      $("critical").innerHTML = tbl(d.critical, rc);

      $("review").innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
          <div>
            <h4 style="margin:0; color:#1e3a8a;">Human Review Governance Queue</h4>
            <div style="font-size:13px; color:#475569; margin-top:2px;">
              <b>${esc(d.review_pending)}</b> High/Critical incident classifications currently awaiting safety officer confirmation or override.
            </div>
          </div>
          <a href="/review" style="text-decoration:none;">
            <button type="button" style="background:#2563eb;">Open Review Queue &rarr;</button>
          </a>
        </div>
      `;
    })
    .catch(err => {
      console.error("Dashboard load failed:", err);
      const asof = document.getElementById("asof");
      if (asof) asof.textContent = "Telemetry sync error. Please check server logs.";
    });
}
