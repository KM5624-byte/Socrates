"use client";

import { useEffect, useRef } from "react";
import { init, use as registerCharts } from "echarts/core";
import { LineChart } from "echarts/charts";
import { AriaComponent, GridComponent, MarkLineComponent, TooltipComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import type { components } from "@aileo/api-client";

registerCharts([LineChart, AriaComponent, GridComponent, MarkLineComponent, TooltipComponent, SVGRenderer]);

export default function SeriesChart({ data, events }: {
  data: components["schemas"]["Series"];
  events: components["schemas"]["PolicyEvent"][];
}) {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const node = container.current;
    if (!node) return;
    const chart = init(node, undefined, { renderer: "svg" });
    function plot() {
      const css = getComputedStyle(document.documentElement);
      const color = (name: string) => css.getPropertyValue(name).trim();
      const markers = [...new Set(events.map((event) => event.date.slice(0, 7)))];
      chart.setOption({
        animation: false,
        textStyle: { color: color("--muted"), fontFamily: "system-ui" },
        aria: { enabled: true, label: { description: `${data.source.dataset_name}, ${data.source.geographic_coverage}. Monthly values and notes are available in the table below.` } },
        grid: { top: 28, bottom: 35, left: 55, right: 22 },
        tooltip: { trigger: "axis", renderMode: "richText", valueFormatter: (value: unknown) =>
          value == null || value === "-" ? "Unavailable" : `${value}${data.source.unit === "percent" ? "%" : " thousand"}` },
        xAxis: { type: "category", boundaryGap: false, data: data.observations.map((row) => row.month),
          axisLine: { lineStyle: { color: color("--line") } }, axisLabel: { hideOverlap: true, color: color("--muted") } },
        yAxis: { type: "value", min: 0, splitNumber: 5,
          axisLabel: { color: color("--muted"), formatter: data.source.unit === "percent" ? "{value}%" : "{value}" },
          splitLine: { lineStyle: { color: color("--line") } } },
        series: [{ type: "line", name: data.source.dataset_name, showSymbol: data.observations.length < 2,
          connectNulls: false, lineStyle: { color: color("--accent"), width: 3 }, itemStyle: { color: color("--accent") },
          data: data.observations.map((row) => row.value),
          markLine: { symbol: "none", silent: true, label: { show: false }, lineStyle: { color: color("--event"), type: "dashed" },
            data: markers.filter((month) => data.observations.some((row) => row.month === month)).map((month) => ({ xAxis: month })) } }],
      });
    }
    const theme = matchMedia("(prefers-color-scheme: dark)");
    const size = new ResizeObserver(() => chart.resize());
    size.observe(node);
    theme.addEventListener("change", plot);
    plot();
    return () => { size.disconnect(); theme.removeEventListener("change", plot); chart.dispose(); };
  }, [data, events]);
  return <div className="chart" ref={container} />;
}
