if (window.DASH) {
  fetch("/api/dashboard")
    .then(r => r.json())
    .then(d => {
      const $ = id => document.getElementById(id);
      const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

      $("asof").innerHTML = `Data as of <b>${esc(d.asof)}</b> <span class="tag" style="margin-left:6px;">Latest Report Timestamp · Demo Clock</span>`;

      // Render KPIs with colored top bars & modern typography
      const K = [
        { label: "Total Reports", val: d.kpi.total, color: "#0284c7", icon: "📋", iconBg: "rgba(2, 132, 199, 0.15)", desc: "All frontline safety observations logged" },
        { label: "SIF Potential", val: d.kpi.sif, color: "#dc2626", icon: "⚠️", iconBg: "rgba(220, 38, 38, 0.15)", desc: `${d.kpi.sif_pct}% of total reports` },
        { label: "High / Critical", val: d.kpi.high_critical, color: "#ea580c", icon: "🚨", iconBg: "rgba(234, 88, 12, 0.15)", desc: `${d.kpi.hc_pct}% of incident volume` },
        { label: "Open Actions", val: d.kpi.open_actions, color: "#ca8a04", icon: "⏳", iconBg: "rgba(202, 138, 4, 0.15)", desc: "Mitigation items undergoing workflow" },
        { label: "Overdue Actions", val: d.kpi.overdue, color: "#e11d48", icon: "⏱️", iconBg: "rgba(225, 29, 72, 0.15)", desc: "SLA escalated to senior management" },
        { label: "Emerging Risks", val: d.kpi.emerging, color: "#7c3aed", icon: "📡", iconBg: "rgba(124, 58, 237, 0.15)", desc: "Statistical 7-day velocity spikes" }
      ];

      if ($("kpis")) {
        $("kpis").innerHTML = K.map(k => `
          <div class="kpi-card">
            <div class="kpi-bar" style="background:${k.color}"></div>
            <div class="kpi-card-top">
              <span class="kpi-label">${esc(k.label)}</span>
              <div class="kpi-icon-wrap" style="background:${k.iconBg}; font-size:15px;">${k.icon}</div>
            </div>
            <div class="kpi-num">${esc(k.val)}</div>
            <div class="kpi-desc">${esc(k.desc)}</div>
          </div>
        `).join("");
      }

      // Render Operational Safety Pulse Strip (5-second situational summary)
      if ($("pulse-grid") && d.pulse) {
        const P = [
          { label: "Total Ingested", val: d.pulse.total_reports, sub: "observations" },
          { label: "SIF Precursors", val: d.pulse.sif_count, sub: `${d.pulse.sif_pct}% volume` },
          { label: "High/Critical Priority", val: d.pulse.hc_count, sub: `${d.pulse.hc_pct}% rate` },
          { label: "Emerging Spikes", val: d.pulse.emerging_count, sub: "active 7d alerts" },
          { label: "Cross-Site Clusters", val: d.pulse.cluster_count, sub: "systemic hazards" },
          { label: "Pending Governance", val: d.pulse.pending_reviews, sub: "reviews needed" },
          { label: "Overdue SLAs", val: d.pulse.overdue_actions, sub: "escalated tasks" }
        ];
        $("pulse-grid").innerHTML = P.map(p => `
          <div class="pulse-item">
            <div class="pulse-item-label">${esc(p.label)}</div>
            <div class="pulse-item-val">${esc(p.val)} <span class="pulse-item-sub">${esc(p.sub)}</span></div>
          </div>
        `).join("");
      }

      // Render Priority Attention Board
      if ($("attention-grid")) {
        const items = [];
        if (d.kpi.overdue > 0) {
          items.push({
            title: "Overdue Corrective Actions",
            badge: `${d.kpi.overdue} Overdue`,
            badgeClass: "CRITICAL",
            desc: `${d.kpi.overdue} corrective actions have exceeded SLA target completion dates and triggered multi-tier escalation.`,
            link: "/actions",
            actionText: "View Actions"
          });
        }
        if (d.review_pending > 0) {
          items.push({
            title: "Pending Human Review",
            badge: `${d.review_pending} In Queue`,
            badgeClass: "HIGH",
            desc: `${d.review_pending} High and Critical incident classifications await safety officer verification or override.`,
            link: "/review",
            actionText: "Open Review Queue"
          });
        }
        if (d.alerts && d.alerts.length > 0) {
          items.push({
            title: "Emerging Risk Spikes",
            badge: `${d.alerts.length} Active`,
            badgeClass: "HIGH",
            desc: `Statistical radar flagged ${d.alerts.length} rapid-increase hazard velocity alerts (≥3 reports and ≥2x prior window).`,
            link: "/alerts",
            actionText: "Inspect Alerts"
          });
        }
        if (d.clusters && d.clusters.length > 0) {
          items.push({
            title: "Systemic Cross-Site Clusters",
            badge: `${d.clusters.length} Hazards`,
            badgeClass: "CRITICAL",
            desc: `Surveillance flagged hazards rising concurrently across ≥3 independent facilities.`,
            link: "/alerts",
            actionText: "Analyze Clusters"
          });
        }
        if (!items.length) {
          $("attention-grid").innerHTML = `<div class="card" style="padding:16px; color:var(--text-muted); grid-column: 1 / -1; text-align:center;">All operations within safe parameters. No urgent SLA breaches or unaddressed high-risk alerts.</div>`;
        } else {
          $("attention-grid").innerHTML = items.map(it => `
            <div class="attention-card">
              <div class="attention-card-top">
                <span class="attention-card-title">${esc(it.title)}</span>
                <span class="badge ${it.badgeClass}" style="font-size:10px;">${esc(it.badge)}</span>
              </div>
              <div class="attention-card-desc">${esc(it.desc)}</div>
              <a href="${it.link}" class="attention-card-action">${esc(it.actionText)} &rarr;</a>
            </div>
          `).join("");
        }
      }

      // Render Emerging Risk Radar Grid
      if ($("emerging-grid")) {
        if (d.alerts && d.alerts.length) {
          $("emerging-grid").innerHTML = d.alerts.map(a => `
            <div class="emerging-card ${String(a.level || '').toLowerCase()}">
              <div class="emerging-card-header">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span class="badge ${a.level}">${esc(a.level)}</span>
                  <span style="font-weight:700; color:#fff; font-size:14px;">${esc(a.site)}</span>
                  <span class="tag" style="background:rgba(56, 189, 248, 0.15); color:var(--brand-cyan); font-weight:700;">${esc(a.hazard)}</span>
                </div>
                <span class="badge ${a.level}">
                  ${a.growth_percent == null ? "NEW SPIKE" : "+" + esc(a.growth_percent) + "%"}
                </span>
              </div>
              <div class="emerging-stats">
                <div class="emerging-stat-item">
                  <div class="emerging-stat-label">Previous 7d</div>
                  <div class="emerging-stat-val">${esc(a.previous_count)}</div>
                </div>
                <div class="emerging-stat-item">
                  <div class="emerging-stat-label">Current 7d</div>
                  <div class="emerging-stat-val" style="color:#ef4444;">${esc(a.current_count)}</div>
                </div>
                <div class="emerging-stat-item">
                  <div class="emerging-stat-label">Velocity</div>
                  <div class="emerging-stat-val" style="color:#f59e0b;">${esc(a.signal || (a.growth_percent != null ? "+" + a.growth_percent + "%" : "NEW SPIKE"))}</div>
                </div>
              </div>
              <div style="font-size:12px; color:var(--text-muted);">${esc(a.reason)}</div>
            </div>
          `).join("");
        } else {
          $("emerging-grid").innerHTML = `<div class="card" style="padding:20px; color:var(--text-muted); grid-column: 1 / -1; text-align:center;">No emerging-risk statistical spikes detected across facilities in the current 7-day window.</div>`;
        }
      }

      // Render Emerging Risk Alerts Box if legacy container exists
      if ($("alertbox")) {
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
      }

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
