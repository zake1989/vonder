import random

verbs = [
    "Mix", "Fold", "Shuffle", "Toggle", "Mangle", "Scan", "Compute", "Process", "Trim", "Evaluate",
  "Check", "Update", "Transform", "Alter", "Randomize", "Merge", "Slice", "Wrap", "Crop", "Hash",
  "Load", "Dump", "Verify", "Rebuild", "Sort", "Inject", "Rotate", "Scale", "Draw", "Clamp",
  "Lock", "Unlock", "Bind", "Unbind", "Attach", "Detach", "Persist", "Parse", "Stream", "Echo",
  "Ping", "Trace", "Filter", "Map", "Reduce", "Expand", "Compress", "Encrypt", "Decrypt", "Sign",
  "Auth", "Refresh", "Clear", "Destroy", "Collect", "Release", "Allocate", "Track", "Print", "Count",
  "Invert", "Replace", "Append", "Prepend", "Split", "Join", "Intersect", "Union", "Patch", "Revoke",
  "Emit", "Flush", "Grow", "Shrink", "Emit", "Balance", "Query", "Index", "Refine", "Stash",
  "Flip", "Slide", "Nudge", "Cluster", "Sortify", "Tag", "Snap", "Drift", "Guard", "Probe",
  "Fuse", "Spark", "Sync", "Drill", "Wrapify", "Log", "Lint", "Batch", "Replay", "Defer"
]

nouns = [
    "Data", "Value", "Token", "Matrix", "Node", "Signal", "Cache", "Option", "List", "Coordinate",
  "Point", "Block", "Seed", "String", "Path", "Request", "Response", "Field", "Record", "Entry",
  "Range", "Item", "Mode", "Flag", "Key", "Cipher", "Vector", "Pixel", "Frame", "Stream",
  "Handle", "Layer", "Module", "Task", "Job", "Slot", "Stage", "Factor", "Hook", "Shell",
  "Trace", "Log", "Spec", "Target", "Cluster", "Segment", "Pair", "Tuple", "Group", "Source",
  "Sink", "Patch", "Route", "Link", "Mesh", "Graph", "Edge", "Anchor", "Batch", "File",
  "Line", "Column", "View", "Theme", "Color", "Theme", "Shape", "Glyph", "Panel", "Tab",
  "Label", "Icon", "Bitmap", "Font", "Stack", "Queue", "Heap", "Map", "Table", "Cell",
  "NodeSet", "Tree", "Branch", "Leaf", "Root", "Chain", "Fence", "Grid", "Cellar", "Vault",
  "Array", "Slice", "Socket", "Port", "Zone", "Pool", "Dock", "Cap", "Form", "Model"
]

templates_with_return = [
  {
    "signature": "func {name}(list: [Double] = []) -> Double",
    "body": [
      "var total = 0.0",
      "for item in list {",
      "total += sqrt(item)",
      "}",
      "return total"
    ]
  },
  {
    "signature": "func {name}(options: [Bool] = []) -> Bool",
    "body": [
      "return options.filter { $0 }.count > 2"
    ]
  },
  {
    "signature": "func {name}(input: String = \"\") -> String",
    "body": [
      "let reversed = String(input.reversed())",
      "return reversed.uppercased()"
    ]
  },
  {
    "signature": "func {name}(flag: Bool = false, count: Int = 0) -> Int",
    "body": [
      "if flag {",
      "return count * 3",
      "} else {",
      "return count / 2",
      "}"
    ]
  },
  {
    "signature": "func {name}(dict: [String: Int] = [:]) -> Int",
    "body": [
      "return dict.values.reduce(0, +)"
    ]
  },
  {
    "signature": "func {name}(bytes: [UInt8] = []) -> UInt8",
    "body": [
      "return bytes.reduce(0, ^)"
    ]
  },
  {
    "signature": "func {name}() -> Date",
    "body": [
      "return Date().addingTimeInterval(Double.random(in: -1000...1000))"
    ]
  },
  {
    "signature": "func {name}(first: String = \"\", second: String = \"\") -> Bool",
    "body": [
      "return first.hasPrefix(second) || second.hasSuffix(first)"
    ]
  },
  {
    "signature": "func {name}(values: Set<Int> = []) -> Int",
    "body": [
      "return values.reduce(1, *)"
    ]
  },
  {
    "signature": "func {name}(array: [Bool] = []) -> Int",
    "body": [
      "var count = 0",
      "for item in array {",
      "if item { count += 1 }",
      "}",
      "return count"
    ]
  },
  {
    "signature": "func {name}() -> UInt32",
    "body": [
      "return arc4random()"
    ]
  },
  {
    "signature": "func {name}(ints: [Int] = [], multiplier: Int = 1) -> [Int]",
    "body": [
      "return ints.map { $0 * multiplier }"
    ]
  },
  {
    "signature": "func {name}(values: [Double] = []) -> Double",
    "body": [
      "guard !values.isEmpty else { return 0 }",
      "return values.reduce(0, +) / Double(values.count)"
    ]
  },
  {
    "signature": "func {name}(data: [Int] = []) -> [Int]",
    "body": [
      "return data.shuffled().prefix(while: { $0 % 2 == 0 })"
    ]
  },
  {
    "signature": "func {name}(text: String = \"\") -> Int",
    "body": [
      "return text.components(separatedBy: \" \").count"
    ]
  },
  {
    "signature": "func {name}(a: Int = 0, b: Int = 0) -> Int",
    "body": [
      "return a > b ? a - b : b - a"
    ]
  },
  {
    "signature": "func {name}(chars: [Character] = []) -> String",
    "body": [
      "return String(chars.shuffled())"
    ]
  },
  {
    "signature": "func {name}(input: Int = 0) -> String",
    "body": [
      "let adjusted = input * 42 - 7",
      "let stringValue = \"\\(adjusted)\"",
      "if stringValue.count > 5 {",
      "return String(stringValue.prefix(5))",
      "}",
      "return stringValue"
    ]
  },
  {
    "signature": "func {name}(values: [Int] = []) -> Int",
    "body": [
      "var sum = 0",
      "for value in values {",
      "sum += value",
      "}",
      "return sum * 3"
    ]
  },
  {
    "signature": "func {name}(text: String = \"\") -> Int",
    "body": [
      "return text.filter { $0.isLetter }.count * 2"
    ]
  },
  {
    "signature": "func {name}(x: Double = 0.0, y: Double = 0.0) -> (Double, Double)",
    "body": [
      "let dx = x + Double.random(in: -1...1)",
      "let dy = y + Double.random(in: -1...1)",
      "return (dx, dy)"
    ]
  },
  {
    "signature": "func {name}() -> Bool",
    "body": [
      "return Bool.random()"
    ]
  },
  {
    "signature": "func {name}(items: [String] = []) -> String",
    "body": [
      "var longest = \"\"",
      "for item in items {",
      "if item.count > longest.count {",
      "longest = item",
      "}",
      "}",
      "return longest"
    ]
  },
  {
    "signature": "func {name}(points: [(Double, Double)] = []) -> Double",
    "body": [
      "var total = 0.0",
      "for (x, y) in points {",
      "total += sqrt(x * x + y * y)",
      "}",
      "return total"
    ]
  },
  {
    "signature": "func {name}(text: String = \"\") -> String",
    "body": [
      "var reversed = \"\"",
      "for char in text.reversed() {",
      "reversed.append(char)",
      "}",
      "return reversed"
    ]
  },
  {
    "signature": "func {name}(values: [Bool] = []) -> Bool",
    "body": [
      "return values.contains(true)"
    ]
  },
  {
    "signature": "func {name}() -> String",
    "body": [
      "let choices = [\"Alpha\", \"Beta\", \"Gamma\"]",
      "return choices.randomElement() ?? \"\""
    ]
  },
  {
    "signature": "func {name}(flag: Bool = false) -> Int",
    "body": [
      "if flag {",
      "return Int.random(in: 0...100)",
      "} else {",
      "return -1",
      "}"
    ]
  },
  {
    "signature": "func {name}(array: [Int] = []) -> [Int]",
    "body": [
      "return array.shuffled()"
    ]
  },
  {
    "signature": "func {name}(path: String = \"\") -> Bool",
    "body": [
      "return path.hasPrefix(\"/tmp\")"
    ]
  },
  {
    "signature": "func {name}(seed: Int = 0) -> UInt64",
    "body": [
      "var result = UInt64(seed)",
      "for _ in 0..<5 {",
      "result = (result &* 31) ^ UInt64.random(in: 0..<1000)",
      "}",
      "return result"
    ]
  },
  {
    "signature": "func {name}(a: Set<Int> = [], b: Set<Int> = []) -> Bool",
    "body": [
      "return a.union(b).count > a.intersection(b).count"
    ]
  },
  {
    "signature": "func {name}(key: String = \"\") -> String",
    "body": [
      "do {",
      "throw NSError(domain: \"Test\", code: 1)",
      "} catch {",
      "return key + \"_fail\"",
      "}"
    ]
  }
]

templates_void = [
  {
    "signature": "func {name}(data: [Int] = [])",
    "body": [
      "_ = data.map { $0 * 2 }"
    ]
  },
  {
    "signature": "func {name}()",
    "body": [
      "defer { _ = UUID() }",
      "_ = Date()"
    ]
  },
  {
    "signature": "func {name}(seconds: Int = 0)",
    "body": [
      "let until = Date().addingTimeInterval(Double(seconds))",
      "while Date() < until { _ = UUID() }"
    ]
  },
  {
    "signature": "func {name}(flag: Bool = false)",
    "body": [
      "var flagVar = flag",
      "flagVar.toggle()",
      "if flagVar {",
      "flagVar = false",
      "} else {",
      "flagVar = true",
      "}"
    ]
  },
  {
    "signature": "func {name}(count: Int = 0)",
    "body": [
      "for i in 0..<count {",
      "_ = i * i",
      "}"
    ]
  },
  {
    "signature": "func {name}()",
    "body": [
      "defer {",
      "let _ = UUID()",
      "}",
      "_ = Date()"
    ]
  },
  {
    "signature": "func {name}(seconds: Double = 0.0)",
    "body": [
      "let until = Date().addingTimeInterval(seconds)",
      "while Date() < until {",
      "_ = UUID()",
      "}"
    ]
  },
  {
    "signature": "func {name}(logs: [String] = [])",
    "body": [
      "var logsCopy = logs",
      "logsCopy.append(\"Log entry at \\(Date())\")"
    ]
  },
  {
    "signature": "func {name}(name: String = \"\")",
    "body": [
      "guard !name.isEmpty else { return }",
      "_ = name.uppercased()"
    ]
  },
  {
    "signature": "func {name}(ints: [Int] = [])",
    "body": [
      "for i in ints { _ = i * i }"
    ]
  },
  {
    "signature": "func {name}(dict: [String: Int] = [:])",
    "body": [
      "for (k, v) in dict { _ = \"\\(k):\\(v)\" }"
    ]
  },
  {
    "signature": "func {name}(flag: Bool = false)",
    "body": [
      "var flagVar = flag",
      "flagVar = !flagVar"
    ]
  },
  {
    "signature": "func {name}(seconds: Double = 0.0)",
    "body": [
      "let end = Date().addingTimeInterval(seconds)",
      "while Date() < end { _ = UUID() }"
    ]
  },
  {
    "signature": "func {name}()",
    "body": [
      "defer { print(\"Deferred\") }"
      "let _ = Date().timeIntervalSince1970"
    ]
  },
  {
    "signature": "func {name}(chars: [Character] = [])",
    "body": [
      "_ = chars.map { String($0).uppercased() }"
    ]
  },
  {
    "signature": "func {name}(multiplier: Int = 1)",
    "body": [
      "for i in 0..<5 { _ = i * multiplier }"
    ]
  },
  {
    "signature": "func {name}(list: [Double] = [])",
    "body": [
      "_ = list.map { sqrt($0) }"
    ]
  },
  {
    "signature": "func {name}(path: String = \"\")",
    "body": [
      "if path.isEmpty { return }",
      "_ = FileManager.default.fileExists(atPath: path)"
    ]
  },
  {
    "signature": "func {name}(data: [Int] = [])",
    "body": [
      "_ = data.shuffled()"
    ]
  },
  {
    "signature": "func {name}()",
    "body": [
      "_ = Date().timeIntervalSince1970"
    ]
  },
  {
    "signature": "func {name}(array: [Int] = [])",
    "body": [
      "for item in array where item % 2 == 0 { _ = item }"
    ]
  },
  {
    "signature": "func {name}(tries: Int = 0)",
    "body": [
      "var attempts = tries",
      "while attempts > 0 {",
      "    attempts -= 1",
      "}"
    ]
  },
  {
    "signature": "func {name}(enabled: Bool = false)",
    "body": [
      "if enabled { _ = UUID() }"
    ]
  },
  {
    "signature": "func {name}(ids: [Int] = [])",
    "body": [
      "for id in ids { _ = id.description }"
    ]
  },
  {
    "signature": "func {name}(letters: [Character] = [])",
    "body": [
      "_ = letters.filter { $0.isLetter }"
    ]
  },
  {
    "signature": "func {name}(notes: [String] = [])",
    "body": [
      "_ = notes.joined(separator: \", \")"
    ]
  },
  {
    "signature": "func {name}(delay: Double = 0.0)",
    "body": [
      "Thread.sleep(forTimeInterval: delay)"
    ]
  }
]

def generate_method(has_return: bool = True) -> str:
    templates = templates_with_return if has_return else templates_void
    template = random.choice(templates)
    
    verb = random.choice(verbs)
    noun = random.choice(nouns)
    method_name = "degention" + verb + noun[0].upper() + noun[1:]
    
    signature = template["signature"].replace("{name}", method_name)
    body_lines = template["body"]
    body = "\n".join("    " + line for line in body_lines)
    
    func_code = f"{signature} {{\n{body}\n}}"
    return func_code