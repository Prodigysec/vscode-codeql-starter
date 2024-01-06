import java
import semmle.code.java.security.AndroidIntentRedirection

from IntentRedirectionFlow::PathNode source, IntentRedirectionFlow::PathNode sink
where IntentRedirectionFlow::flowPath(source, sink)
select sink.getNode(), source, sink,
  "Arbitrary Android activities or services can be started from a $@.", source.getNode(),
  "user-provided value"

