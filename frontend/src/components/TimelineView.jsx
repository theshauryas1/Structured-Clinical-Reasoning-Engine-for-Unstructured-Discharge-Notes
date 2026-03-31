const SECTION_LABELS = {
  admission: "Admission",
  hospital_course: "Hospital course",
  discharge: "Discharge",
};

export default function TimelineView({ timeline }) {
  if (!timeline?.sections?.length) {
    return <p className="empty-state">Run the pipeline to render the timeline.</p>;
  }

  return (
    <div className="timeline-row">
      {timeline.sections.map((section) => (
        <article className="timeline-column" key={section.name}>
          <div className="timeline-heading">
            <span>{SECTION_LABELS[section.name] || section.name}</span>
            <strong>{section.events.length} events</strong>
          </div>
          <p className="timeline-text">{section.text}</p>
          <div className="event-stack">
            {section.events.map((event) => (
              <div className="event-chip" key={`${event.start}-${event.end}`}>
                <span className={`event-label event-${event.label.toLowerCase()}`}>
                  {event.label}
                </span>
                <strong>{event.text}</strong>
                <small>
                  {event.status} • {event.domain}
                </small>
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
