// Public regression writer. It touches only the new test path supplied by pytest.
import Foundation
import Darwin
let path = CommandLine.arguments[1]
let coordinator = NSFileCoordinator(filePresenter: nil)
var error: NSError?
var completed = false
coordinator.coordinate(writingItemAt: URL(fileURLWithPath: path), options: [], error: &error) { url in
    print("WRITER_ENTERED")
    fflush(stdout)
    guard FileHandle.standardInput.readData(ofLength: 5) == Data("DONE\n".utf8) else { return }
    do {
        try Data("{\"public\":true}\n".utf8).write(to: url)
        completed = true
    } catch { return }
}
if error != nil || !completed { exit(3) }
print("WRITER_RETURNED")
