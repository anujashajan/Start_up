import { useState } from "react";
import type { InventoryRow, OrderRow } from "../api";

export default function InventoryOrders({ inventory, orders }: { inventory: InventoryRow[] | null; orders: OrderRow[] | null }) {
  const [tab, setTab] = useState<"inventory" | "orders">("inventory");

  return (
    <div>
      <div className="mb-2 flex gap-1">
        <button
          onClick={() => setTab("inventory")}
          className={`rounded-full px-3 py-1 text-[11px] ${tab === "inventory" ? "bg-sky-500/15 text-sky-300" : "text-slate-500"}`}
        >
          Inventory
        </button>
        <button
          onClick={() => setTab("orders")}
          className={`rounded-full px-3 py-1 text-[11px] ${tab === "orders" ? "bg-sky-500/15 text-sky-300" : "text-slate-500"}`}
        >
          Orders
        </button>
      </div>

      {tab === "inventory" ? (
        <div className="max-h-[260px] overflow-y-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead className="sticky top-0 bg-slate-950 text-slate-500">
              <tr>
                <th className="px-2 py-1.5 font-medium">Part</th>
                <th className="px-2 py-1.5 font-medium">Line</th>
                <th className="px-2 py-1.5 font-medium">On Hand</th>
                <th className="px-2 py-1.5 font-medium">Reorder Pt.</th>
              </tr>
            </thead>
            <tbody>
              {inventory?.map((i) => (
                <tr key={i.part_number} className="border-t border-slate-800/60">
                  <td className="px-2 py-1.5 text-slate-300">{i.part_name}</td>
                  <td className="px-2 py-1.5 text-slate-500">{i.line}</td>
                  <td className={`px-2 py-1.5 ${i.below_reorder ? "text-rose-400" : "text-slate-300"}`}>{i.qty_on_hand}</td>
                  <td className="px-2 py-1.5 text-slate-500">{i.reorder_point}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="max-h-[260px] overflow-y-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead className="sticky top-0 bg-slate-950 text-slate-500">
              <tr>
                <th className="px-2 py-1.5 font-medium">Customer</th>
                <th className="px-2 py-1.5 font-medium">Part</th>
                <th className="px-2 py-1.5 font-medium">Qty</th>
                <th className="px-2 py-1.5 font-medium">Due</th>
              </tr>
            </thead>
            <tbody>
              {orders?.map((o) => (
                <tr key={o.id} className="border-t border-slate-800/60">
                  <td className="px-2 py-1.5 text-slate-300">{o.customer}</td>
                  <td className="px-2 py-1.5 text-slate-500">{o.part_name}</td>
                  <td className="px-2 py-1.5 text-slate-300">{o.qty}</td>
                  <td className="px-2 py-1.5 text-slate-500">{new Date(o.due_date).toLocaleDateString("en-IN")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
