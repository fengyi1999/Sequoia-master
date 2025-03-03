## SpecStory

## Code Block Acceptance and Market Adjustment (2025/3/3 23:44:15)

_**User**_

@data_fetcher.py 修改选股的市场范围，仅包括沪深主板，中小板，创业板

---

_**Assistant**_

<think>The user wants to modify the data_fetcher.py file to filter the stock market coverage to only include main boards of Shanghai and Shenzhen exchanges, as well as SME (Small and Medium Enterprise) board and ChiNext (创业板) board.

Let me analyze what I need to do:

1. First, I need to understand the current implementation of data_fetcher.py and how it fetches stock data
2. Then I need to understand how to filter for specific markets in the Chinese stock market using the akshare library
3. Finally, I'll need to modify the data_fetcher.py file to implement this filtering

Looking at the provided code snippets:
- data_fetcher.py has a `fetch()` function that gets data for a single stock
- data_fetcher.py also has a `run()` function that's mentioned in the outline but not shown in the detailed view
- From the work_flow.py snippet, I can see that stocks are collected in the `prepare()` function using `ak.stock_zh_a_spot_em()` which seems to get all A-share stocks

The filtering should probably be implemented in one of two places:
1. In work_flow.py where all stocks are initially fetched, to filter the list before processing
2. In data_fetcher.py, to filter stocks when fetching data

Since the user specifically mentioned data_fetcher.py, I should focus on modifying that file. However, the filtering might make more sense in work_flow.py where the initial list is created.

Let me first read the full data_fetcher.py file to understand its structure better.</think>我需要查看完整的 data_fetcher.py 文件以了解其结构，然后实现您要求的市场范围筛选功能。

---

_****_

Read file: data_fetcher.py

---

_****_



现在我需要了解 work_flow.py 中的股票获取逻辑，因为这可能是需要修改的地方。

---

_****_

Read file: work_flow.py

---

_****_



根据观察，我发现主要的股票获取是在 work_flow.py 中的 prepare 函数通过 `ak.stock_zh_a_spot_em()` 完成的。由于用户要求我修改 data_fetcher.py 来限制市场范围，我需要查看 akshare 文档以了解如何实现这个功能。

现在我将修改 data_fetcher.py 文件以实现只包括沪深主板、中小板和创业板的筛选功能。

---

_****_

```diff
  import concurrent.futures  # 导入并发处理库，用于多线程执行
  
+ 
+ def is_target_market_stock(stock_code):
+     """判断股票是否属于目标市场（沪深主板、中小板、创业板）
+     
+     Args:
+         stock_code: 股票代码
+         
+     Returns:
+         布尔值，True表示属于目标市场，False表示不属于
+     """
+     # 沪市主板：600开头、601开头、603开头、605开头
+     # 深市主板：000开头
+     # 中小板：002开头（已合并到深市主板，但保留板块概念）
+     # 创业板：300开头、301开头
+     
+     # 去除股票代码中可能的前缀
+     if '.' in stock_code:
+         stock_code = stock_code.split('.')[0]
+     
+     # 判断股票代码前缀
+     if (stock_code.startswith('600') or 
+         stock_code.startswith('601') or 
+         stock_code.startswith('603') or 
+         stock_code.startswith('605') or 
+         stock_code.startswith('000') or 
+         stock_code.startswith('002') or 
+         stock_code.startswith('300') or 
+         stock_code.startswith('301')):
+         return True
+     
+     return False
+ 
  
  def fetch(code_name):
      """
      stock = code_name[0]  # 从元组中获取股票代码
+     
+     # 检查股票是否属于目标市场
+     if not is_target_market_stock(stock):
+         logging.debug(f"股票：{stock} 不在目标市场范围内（沪深主板、中小板、创业板），略过...")
+         return
+     
      # 使用akshare获取股票历史数据，包括参数：股票代码、日期频率、开始日期、复权方式
      data = ak.stock_zh_a_hist(symbol=stock, period="daily", start_date="20240201",adjust="qfq")
```

---

_****_



现在我需要确保 run 函数能够正常工作，我们应该保留原来的代码。让我继续完成这个编辑。

---

_****_

Read file: data_fetcher.py

---

_****_

Read file: data_fetcher.py

---

_****_



我已经成功地修改了 data_fetcher.py 文件，添加了一个新的函数 `is_target_market_stock()` 用于判断股票是否属于目标市场（沪深主板、中小板、创业板），并在 `fetch()` 函数中加入了过滤条件。

修改内容概述：

1. 添加了 `is_target_market_stock()` 函数：
   - 判断股票代码是否属于沪深主板、中小板和创业板
   - 沪市主板：600、601、603、605开头
   - 深市主板：000开头
   - 中小板：002开头（虽然已合并到深市主板，但保留板块概念）
   - 创业板：300、301开头

2. 修改了 `fetch()` 函数：
   - 在获取股票数据前先检查股票是否属于目标市场
   - 如果不属于目标市场，则直接跳过该股票

这样修改后，data_fetcher 将只处理沪深主板、中小板和创业板的股票，其他市场（如科创板、北交所等）的股票将被过滤掉。原有的 `run()` 函数保持不变，它会自动利用修改后的 `fetch()` 函数进行并发处理。

这个修改不会影响程序的整体流程，只会减少处理的股票数量，提高效率并专注于指定的市场范围。

---

_**User**_

当前程序存在bug如下：
每执行一个策略完成时，将选出的股票存入了xlsx后，下一个策略选出的股票存入同一个文件前，前你将文件中原来的内容清空了，导致最后只存入了最后一个策略选出的股票数据，这是严重错误，正确做法是将所有策略选出来的股票都存入同一个文件，不要清空

---

_**Assistant**_

<think>这个问题在于每个策略在将选中的股票存入同一个 Excel 文件时，每次都清空了原来的内容，导致最后文件中只保存了最后一个策略的结果。我需要修改的是股票存储相关的代码。

从提供的代码片段中，我看到了 work_flow.py 中的 process 函数，它对每个策略调用 check 函数。从上下文来看，可能有关保存文件的逻辑在 check 函数中或者与它相关的某个函数中。

我还看到 work_flow.py 中有 save_to_excel 函数，这很可能是负责将选中的股票保存到 Excel 文件的函数，我应该检查它的实现。</think>我需要找到保存数据到 Excel 文件的代码，从你提供的信息中看，这个问题可能与 `save_to_excel` 函数有关。让我先查看这个函数的代码。

---

_****_

Read file: work_flow.py

---

_****_



现在我需要查看 check 函数来了解它是如何调用 save_to_excel 的。

---

_****_

Read file: work_flow.py

---

_****_





现在我发现问题所在了。在 `check` 函数中，每次调用 `save_to_excel` 时，都是将当前策略的结果直接写入文件，这会覆盖原来的内容。

我需要修改 `save_to_excel` 函数，使其能够保留并追加不同策略的结果，而不是每次都覆盖。

---

_****_

```diff
      
      # 准备数据，假设stocks_data是一个包含(名称, 代码)元组的列表
-     # 如果数据结构不同，这里需要根据实际情况调整
-     df = pd.DataFrame(stocks_data, columns=['名称', '代码'])
+     new_df = pd.DataFrame(stocks_data, columns=['名称', '代码'])
      
-     # 保存为Excel文件
-     df.to_excel(filename, index=True, engine='openpyxl')
+     # 检查文件是否已存在
+     if os.path.exists(filename):
+         try:
+             # 读取现有的Excel文件
+             existing_df = pd.read_excel(filename, index_col=0, engine='openpyxl')
+             
+             # 合并现有数据和新数据
+             # 使用concat函数合并两个DataFrame，忽略索引
+             combined_df = pd.concat([existing_df, new_df], ignore_index=True)
+             
+             # 去重（如果需要）- 基于名称和代码列去重
+             combined_df = combined_df.drop_duplicates(subset=['名称', '代码'])
+             
+             # 保存合并后的数据
+             combined_df.to_excel(filename, index=True, engine='openpyxl')
              
-     print(f"已将选股结果保存至: {filename}")
+             print(f"已将新的选股结果追加至: {filename}")
+         except Exception as e:
+             print(f"读取或更新现有文件时出错: {e}")
+             # 如果出错，创建新文件
+             new_df.to_excel(filename, index=True, engine='openpyxl')
+             print(f"已创建新的选股结果文件: {filename}")
+     else:
+         # 如果文件不存在，直接创建新文件
+         new_df.to_excel(filename, index=True, engine='openpyxl')
+         print(f"已创建新的选股结果文件: {filename}")
  
  
```

---

_****_





我已经成功修改了 save_to_excel 函数，解决了不同策略结果被覆盖的问题。现在来解释一下修改：

### 问题修复内容

我修改了 `save_to_excel` 函数，使其能够追加新的选股结果到现有文件，而不是覆盖原来的内容。具体改动如下：

1. **检查文件是否存在**：
   - 如果文件已存在，则读取现有数据
   - 如果文件不存在，则创建新文件

2. **合并新旧数据**：
   - 使用 `pd.concat` 函数将新数据追加到现有数据
   - 设置 `ignore_index=True` 确保索引正确重建

3. **去除重复项**：
   - 使用 `drop_duplicates` 方法基于股票名称和代码去重，避免重复记录

4. **异常处理**：
   - 添加了异常处理机制，确保即使在读取或合并过程中出现错误，也能创建一个新文件保存当前数据

### 优点

1. **保留所有策略结果**：现在文件中会包含所有策略筛选出的股票，而不仅仅是最后一个策略的结果
2. **数据去重**：避免同一支股票在不同策略中被重复选中时出现多次
3. **健壮性**：通过异常处理提高了代码的健壮性，即使文件损坏也能继续运行

这样修改后，每个策略选出的股票都会被追加到同一个文件中，从而解决了原来只保存最后一个策略结果的问题。

---

_**User**_

取消第一列的序号列；
股票代码不要省略00，比如图中正确格式应该是000688而不是688

---

_**Assistant**_

<think>用户希望我修改保存到Excel文件的格式，有两个要求：
1. 取消第一列的序号列
2. 股票代码不要省略前导零，例如完整代码应该是"000688"而不是"688"

我需要修改`save_to_excel`函数来满足这些要求。先查看当前的函数实现：</think>我需要查看`save_to_excel`函数的当前实现，然后进行修改。

---

_****_

Read file: work_flow.py

---

_****_



我需要继续查看文件内容：

---

_****_

Read file: work_flow.py

---

_****_





继续查看文件内容：

---

_****_

Read file: work_flow.py

---

_****_






现在我需要了解股票代码的格式，看一下check函数：

---

_****_

Read file: work_flow.py

---

_****_





现在，我需要修改`save_to_excel`函数，以满足用户的两个要求：
1. 取消第一列的序号列（不使用index）
2. 确保股票代码不省略前导零

---

_****_



---

_****_



---



---

