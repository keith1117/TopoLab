// Exact-file read coordination only. Source content remains in the Python reader.
import Foundation
import Darwin

func clockNS() -> Int64 {
    var value = timespec()
    clock_gettime(CLOCK_REALTIME, &value)
    return Int64(value.tv_sec) * 1_000_000_000 + Int64(value.tv_nsec)
}

func emit(_ value: [String: Any], error: Bool = false) {
    do {
        let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
        let stream = error ? FileHandle.standardError : FileHandle.standardOutput
        stream.write(data)
        stream.write(Data([10]))
    } catch {
        exit(70)
    }
}

guard CommandLine.arguments.count == 2 else { exit(64) }
let requested = CommandLine.arguments[1]
let url = URL(fileURLWithPath: requested)
guard requested.hasPrefix("/"), url.path == requested,
      !requested.split(separator: "/").contains(".."),
      !requested.split(separator: "/").contains(".") else { exit(64) }
let coordinator = NSFileCoordinator(filePresenter: nil)
var coordinationError: NSError?
var completed = false
var entered = false
coordinator.coordinate(readingItemAt: url, options: [], error: &coordinationError) { accessor in
    // A different URL requires another frozen provenance route; do not follow it.
    guard accessor.path == requested else {
        emit(["event": "accessor_url_refused", "requested_url": requested,
              "accessor_url": accessor.path, "pid": getpid()], error: true)
        return
    }
    entered = true
    emit(["event": "accessor_entered", "requested_url": url.absoluteString,
          "accessor_url": accessor.absoluteString, "pid": getpid(), "entered_ns": clockNS()])
    let acknowledgment = FileHandle.standardInput.readData(ofLength: 5)
    guard acknowledgment == Data("DONE\n".utf8) else {
        emit(["event": "reader_ack_refused", "pid": getpid()], error: true)
        return
    }
    completed = true
}
if let error = coordinationError {
    emit(["event": "coordination_error", "pid": getpid(), "domain": error.domain,
          "code": error.code, "description": error.localizedDescription], error: true)
    exit(2)
}
guard entered && completed else { exit(3) }
emit(["event": "accessor_returned", "pid": getpid(), "left_ns": clockNS()])
