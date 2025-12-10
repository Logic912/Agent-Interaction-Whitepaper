# dynamic_smart_society.py - 完整可运行版本
import random
import numpy as np
from collections import defaultdict

print("🎲 智能体社会 v2.0 - 动态演化系统")
print("=" * 80)

# ========== 参数配置 ==========
DAYS_TO_SIMULATE = 30
INITIAL_CAPITAL = 800

# 公司能力护照
COMPANIES = {
    "A": {
        "name": "卓越科技",
        "quality": "high",
        "defect_rate": 0.01,
        "base_price": 10,
        "base_profit": 5,
        "defect_counter": 0,
        "defects_trigger": 100,
        "color": "🔵"
    },
    "B": {
        "name": "平衡方案",
        "quality": "medium",
        "defect_rate": 0.02,
        "base_price": 8,
        "base_profit": 4,
        "defect_counter": 0,
        "defects_trigger": 50,
        "color": "🟢"
    },
    "C": {
        "name": "经济优选",
        "quality": "low",
        "defect_rate": 0.10,
        "base_price": 5,
        "base_profit": 3,
        "defect_counter": 0,
        "defects_trigger": 10,
        "color": "🟡"
    }
}


# ========== 购买者需求类 ==========
class BuyerDemand:
    def __init__(self):
        self.base = 95
        self.trend = 0.1
        self.seasonality_amp = 3
        self.seasonality_period = 7
        self.noise_std = 2
        self.demand_history = []
        self.actual_purchase_history = []

    def generate_true_demand(self, day):
        trend_component = self.trend * day
        season_component = self.seasonality_amp * np.sin(2 * np.pi * day / self.seasonality_period)
        noise_component = random.gauss(0, self.noise_std)
        true_demand = self.base + trend_component + season_component + noise_component
        true_demand = int(np.clip(true_demand, 90, 110))
        self.demand_history.append((day, true_demand))
        return true_demand

    def actual_purchase(self, day, available_tasks, defects_today):
        true_demand = self.generate_true_demand(day)
        reduction = defects_today * 10
        desired_purchase = max(0, true_demand - reduction)
        actual = min(desired_purchase, available_tasks)
        self.actual_purchase_history.append((day, actual, true_demand, reduction))
        return actual, true_demand, reduction


# ========== 残次品生成器 ==========
class DefectGenerator:
    @staticmethod
    def generate_defects(company_id, production_count):
        company = COMPANIES[company_id]
        total_defects = 0
        remaining_production = production_count

        while remaining_production > 0:
            needed_for_next_defect = company["defects_trigger"] - company["defect_counter"]
            if remaining_production >= needed_for_next_defect:
                total_defects += 1
                remaining_production -= needed_for_next_defect
                company["defect_counter"] = 0
            else:
                company["defect_counter"] += remaining_production
                remaining_production = 0

        company.setdefault("total_defects", 0)
        company["total_defects"] = company.get("total_defects", 0) + total_defects
        company.setdefault("defect_history", []).append({
            "day": len(company.get("defect_history", [])) + 1,
            "production": production_count,
            "defects": total_defects
        })

        return total_defects


# ========== 任务发布者 ==========
class TaskPublisher:
    def __init__(self, name="发布者中心"):
        self.name = name
        self.daily_capital = INITIAL_CAPITAL
        self.total_profit = 0
        self.strategy_history = []
        self.contracts_today = {"A": 0, "B": 0, "C": 0}

    def reset_daily(self):
        self.daily_capital = INITIAL_CAPITAL
        self.contracts_today = {"A": 0, "B": 0, "C": 0}

    def calculate_optimal_allocation(self, tasks_needed, company_capacities):
        best_allocation = {"A": 0, "B": 0, "C": 0}
        best_profit = 0

        max_a = min(company_capacities["A"], self.daily_capital // COMPANIES["A"]["base_price"])
        for a in range(max_a + 1):
            cost_a = a * COMPANIES["A"]["base_price"]
            remaining_after_a = self.daily_capital - cost_a

            max_b = min(company_capacities["B"], remaining_after_a // COMPANIES["B"]["base_price"])
            for b in range(max_b + 1):
                cost_b = b * COMPANIES["B"]["base_price"]
                remaining_after_b = remaining_after_a - cost_b

                max_c = min(company_capacities["C"], remaining_after_b // COMPANIES["C"]["base_price"])
                for c in range(max_c + 1):
                    total_cost = cost_a + cost_b + c * COMPANIES["C"]["base_price"]
                    total_tasks = a + b + c

                    if total_tasks > tasks_needed:
                        continue

                    total_profit = (a * COMPANIES["A"]["base_profit"] +
                                    b * COMPANIES["B"]["base_profit"] +
                                    c * COMPANIES["C"]["base_profit"])

                    if total_profit > best_profit or (
                            total_profit == best_profit and total_tasks < sum(best_allocation.values())):
                        best_profit = total_profit
                        best_allocation = {"A": a, "B": b, "C": c}

        return best_allocation, best_profit

    def publish_tasks(self, day, tasks_needed, company_capacities):
        print(f"\n📅 第{day}天开始")
        print(f"  任务需求: {tasks_needed}个 | 起始资金: {self.daily_capital}金币")
        print(f"  公司产能: A={company_capacities['A']}, B={company_capacities['B']}, C={company_capacities['C']}")

        allocation, expected_profit = self.calculate_optimal_allocation(tasks_needed, company_capacities)
        total_cost = (allocation["A"] * COMPANIES["A"]["base_price"] +
                      allocation["B"] * COMPANIES["B"]["base_price"] +
                      allocation["C"] * COMPANIES["C"]["base_price"])
        total_tasks = sum(allocation.values())

        print(f"\n  📊 最优分配方案:")
        print(f"    {COMPANIES['A']['color']} A公司: {allocation['A']}个任务 (成本:{allocation['A'] * 10}金币)")
        print(f"    {COMPANIES['B']['color']} B公司: {allocation['B']}个任务 (成本:{allocation['B'] * 8}金币)")
        print(f"    {COMPANIES['C']['color']} C公司: {allocation['C']}个任务 (成本:{allocation['C'] * 5}金币)")
        print(f"    总计: {total_tasks}个任务 | 总成本: {total_cost}金币 | 预期利润: {expected_profit}金币")

        unmet = tasks_needed - total_tasks
        if unmet > 0:
            print(f"  ⚠️  警告: 资金不足，{unmet}个任务无法发布")

        strategy = {
            "day": day,
            "allocation": allocation.copy(),
            "tasks_needed": tasks_needed,
            "total_tasks": total_tasks,
            "total_cost": total_cost,
            "expected_profit": expected_profit,
            "unmet_demand": unmet
        }
        self.strategy_history.append(strategy)
        self.contracts_today = allocation
        self.daily_capital -= total_cost

        return allocation, expected_profit, total_tasks


# ========== 预测系统 ==========
class PublisherPredictor:
    def __init__(self):
        self.observation_history = []
        self.prediction_history = []

    def observe(self, day, actual_purchase, defects_yesterday):
        self.observation_history.append({
            "day": day,
            "actual": actual_purchase,
            "defects": defects_yesterday
        })

    def predict_demand(self, day):
        if day <= 1:
            return 95

        history_days = min(day - 1, 7)
        recent_data = self.observation_history[-history_days:]

        if len(recent_data) < 2:
            return np.mean([d["actual"] for d in recent_data]) if recent_data else 95

        recent_actuals = [d["actual"] + d["defects"] * 10 for d in recent_data]
        days = [d["day"] for d in recent_data]
        actuals = recent_actuals

        try:
            coeff = np.polyfit(days, actuals, 1)
            linear_pred = np.polyval(coeff, day)
        except:
            linear_pred = np.mean(actuals)

        same_weekday_vals = []
        for d in self.observation_history:
            if d["day"] % 7 == day % 7:
                same_weekday_vals.append(d["actual"] + d["defects"] * 10)

        seasonal_pred = np.mean(same_weekday_vals) if same_weekday_vals else linear_pred
        ma_pred = np.mean(recent_actuals)
        combined = linear_pred * 0.3 + seasonal_pred * 0.5 + ma_pred * 0.2

        uncertainty = max(3, 10 - len(self.observation_history) / 3)
        final_pred = int(combined + random.gauss(0, uncertainty))

        self.prediction_history.append({
            "day": day,
            "prediction": final_pred
        })

        return max(90, min(110, final_pred))


# ========== 公司类 ==========
class Company:
    def __init__(self, company_id):
        self.id = company_id
        self.info = COMPANIES[company_id]
        self.daily_capacity = 0
        self.assigned_tasks = 0
        self.actual_production = 0
        self.defects_produced = 0
        self.total_income = 0
        self.total_production = 0
        self.total_defects = 0
        self.defect_damage_history = []

    def set_daily_capacity(self):
        if self.id == "A":
            self.daily_capacity = random.randint(30, 50)
        elif self.id == "B":
            self.daily_capacity = random.randint(35, 45)

    def produce(self, assigned_tasks):
        self.assigned_tasks = min(assigned_tasks, self.daily_capacity)
        self.actual_production = self.assigned_tasks
        self.defects_produced = DefectGenerator.generate_defects(self.id, self.actual_production)
        good_products = self.actual_production - self.defects_produced

        self.total_production += self.actual_production
        self.total_defects += self.defects_produced
        self.total_income += self.actual_production * self.info["base_price"]

        return good_products, self.defects_produced

    def calculate_daily_loss(self, defects_produced):
        if defects_produced == 0:
            return 0
        lost_sales = defects_produced * 10
        avg_profit_per_task = 4
        return lost_sales * avg_profit_per_task


# ========== 仲裁系统 ==========
class FinalArbitration:
    def __init__(self):
        self.damage_records = defaultdict(list)
        self.total_damages = defaultdict(float)
        self.penalties = {}

    def record_damage(self, company_id, day, damage_amount):
        self.damage_records[company_id].append((day, damage_amount))
        self.total_damages[company_id] = self.total_damages.get(company_id, 0) + damage_amount

    def calculate_penalties(self, day):
        if day != 30:
            return {}

        print("\n" + "=" * 80)
        print("⚖️  最终仲裁日 - 第30天损失清算")
        print("=" * 80)

        for company_id in ["A", "B", "C"]:
            damage = self.total_damages.get(company_id, 0)
            penalty = damage * 0.9

            self.penalties[company_id] = {
                "total_damage": damage,
                "penalty_amount": penalty,
                "penalty_rate": 0.9,
                "damage_days": len(self.damage_records.get(company_id, []))
            }

            if damage > 0:
                print(f"\n{COMPANIES[company_id]['color']} {company_id}公司:")
                print(f"  累计造成损失: {damage:.1f}金币")
                print(f"  罚款金额: {penalty:.1f}金币 (90%)")

        return self.penalties


# ========== 主模拟类 ==========
class DynamicSmartSociety:
    def __init__(self):
        self.publisher = TaskPublisher()
        self.companies = {id: Company(id) for id in ["A", "B", "C"]}
        self.buyer_demand = BuyerDemand()
        self.predictor = PublisherPredictor()
        self.arbitration = FinalArbitration()
        self.day = 0
        self.total_defects_tomorrow = 0
        self.yesterday_defects = 0
        self.daily_results = []

    def generate_daily_capacities(self):
        capacities = {}
        remaining = 120
        capacities["A"] = random.randint(30, 50)
        remaining -= capacities["A"]
        capacities["B"] = random.randint(30, min(50, remaining - 10))
        remaining -= capacities["B"]
        capacities["C"] = remaining
        return capacities

    def run_day(self):
        self.day += 1

        print(f"\n{'=' * 60}")
        print(f"📅 第{self.day}天开始")
        print(f"{'=' * 60}")

        # 预测需求
        predicted_demand = self.predictor.predict_demand(self.day)
        print(f"\n🔮 发布者预测:")
        print(f"  预测需求: {predicted_demand}个任务")
        print(f"  昨日残次品影响: {self.yesterday_defects}个 → 今天减少购买 {self.yesterday_defects * 10}个")

        # 重置
        self.publisher.reset_daily()
        capacities = self.generate_daily_capacities()
        for id, cap in capacities.items():
            self.companies[id].daily_capacity = cap

        print(f"\n🏭 公司产能:")
        for id in ["A", "B", "C"]:
            print(f"  {COMPANIES[id]['color']} {id}: {capacities[id]}个任务")

        # 分配任务
        allocation, expected_profit, tasks_published = self.publisher.publish_tasks(
            self.day, predicted_demand, capacities
        )

        # 生产
        today_defects = {}
        total_good_products = 0

        print(f"\n🏭 生产结果:")
        for id in ["A", "B", "C"]:
            assigned = allocation.get(id, 0)
            if assigned > 0:
                good, defects = self.companies[id].produce(assigned)
                today_defects[id] = defects
                total_good_products += good

                if defects > 0:
                    print(f"  {COMPANIES[id]['color']} {id}: 生产{assigned}个，残次品{defects}个")
                    damage = self.companies[id].calculate_daily_loss(defects)
                    self.arbitration.record_damage(id, self.day, damage)
                else:
                    print(f"  {COMPANIES[id]['color']} {id}: 生产{assigned}个，全部合格")

        # 购买
        available_for_sale = total_good_products
        actual_purchase, true_demand, reduction = self.buyer_demand.actual_purchase(
            self.day, available_for_sale, self.yesterday_defects
        )

        # 计算利润
        actual_profit = 0
        actual_cost = 0
        temp_purchase = actual_purchase

        for id in ["A", "B", "C"]:
            sold = min(allocation.get(id, 0), temp_purchase)
            temp_purchase -= sold
            actual_profit += sold * COMPANIES[id]["base_profit"]
            actual_cost += sold * COMPANIES[id]["base_price"]

        # 学习
        self.predictor.observe(self.day, actual_purchase, self.yesterday_defects)
        total_defects_today = sum(today_defects.values())
        self.yesterday_defects = total_defects_today

        # 记录
        result = {
            "day": self.day,
            "predicted_demand": predicted_demand,
            "true_demand": true_demand,
            "tasks_published": tasks_published,
            "allocation": allocation.copy(),
            "total_good_products": total_good_products,
            "defects_today": total_defects_today,
            "yesterday_defects_effect": reduction,
            "actual_purchase": actual_purchase,
            "actual_profit": actual_profit,
            "expected_profit": expected_profit
        }

        self.daily_results.append(result)

        # 日报
        print(f"\n💰 第{self.day}天结果:")
        print(f"  真实需求: {true_demand}个")
        print(f"  残次品影响: -{reduction}个购买")
        print(f"  实际购买: {actual_purchase}个")
        print(f"  良品生产: {total_good_products}个")
        print(f"  今日残次品: {total_defects_today}个（明天生效）")
        print(f"  今日利润: {actual_profit}金币")

        return result

    def run_simulation(self, days):
        print(f"\n🚀 开始{days}天动态演化模拟")
        print("=" * 80)

        for _ in range(days):
            self.run_day()

        if days >= 30:
            self.arbitration.calculate_penalties(days)

        return self.daily_results

    def print_analysis(self):
        print("\n" + "=" * 80)
        print("📊 动态系统分析报告")
        print("=" * 80)

        # 预测准确性
        pred_errors = []
        for r in self.daily_results:
            error = abs(r["predicted_demand"] - r["true_demand"])
            pred_errors.append(error)

        print(f"\n🔮 预测性能:")
        print(f"  平均绝对误差: {np.mean(pred_errors):.1f}个")

        # 残次品统计
        total_defects = sum(r["defects_today"] for r in self.daily_results)
        print(f"\n⚠️  残次品统计:")
        print(f"  总残次品: {total_defects}个")

        # 公司表现
        print(f"\n🏢 公司累计表现:")
        for id in ["A", "B", "C"]:
            company = self.companies[id]
            print(f"\n  {COMPANIES[id]['color']} {id}公司:")
            print(f"    总生产: {company.total_production}个")
            print(f"    总收入: {company.total_income}金币")
            print(
                f"    总残次品: {company.total_defects}个 ({company.total_defects / max(1, company.total_production) * 100:.1f}%)")

            if id in self.arbitration.total_damages:
                damage = self.arbitration.total_damages[id]
                print(f"    造成损失: {damage:.1f}金币")

        # 系统效率
        total_profit = sum(r["actual_profit"] for r in self.daily_results)
        total_possible = sum(r["true_demand"] for r in self.daily_results) * 4
        efficiency = total_profit / total_possible * 100 if total_possible > 0 else 0

        print(f"\n📈 系统效率:")
        print(f"  实际总利润: {total_profit}金币")
        print(f"  系统效率: {efficiency:.1f}%")


# ========== 运行模拟 ==========
if __name__ == "__main__":
    society = DynamicSmartSociety()
    results = society.run_simulation(30)
    society.print_analysis()

    print("\n" + "=" * 80)
    print("✅ 动态演化模型验证完成!")
    print("=" * 80)
