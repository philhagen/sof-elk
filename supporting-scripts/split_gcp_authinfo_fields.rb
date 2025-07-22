# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script reformats the GCP "authorizationInfo" field into more a more searchable structure
# for example (key_field = "permission"):
# - source: [{"resource":"billingAccounts/019921-BE6AE6-562F1C","permission":"billing.resourceAssociations.create","granted":true,"resourceAttributes":{}},{"resource":"projects/suit-ai","permission":"resourcemanager.projects.createBillingAssignment","granted":true,"resourceAttributes":{}},{"resource":"projects/suit-ai","permission":"resourcemanager.projects.deleteBillingAssignment","granted":true,"resourceAttributes":{}}]
# - result: {"billing.resourceAssociations.create":[{"resource":"billingAccounts/019921-BE6AE6-562F1C","granted":true},{"resource":"billingAccounts/019921-BE6AE6-562F1C","granted":true}],"resourcemanager.projects.createBillingAssignment":[{"resource":"projects/suit-ai","granted":true}],"resourcemanager.projects.deleteBillingAssignment":[{"resource":"projects/suit-ai","granted":true}]}

# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
    @source_field = params["source_field"]
    @destination_field = params["destination_field"]
    @key_field = params["key_field"]
end

# the filter method receives an event and must return a list of events.
# Dropping an event means not including it in the return array,
# while creating new ones only requires you to add a new instance of
# LogStash::Event to the returned array
def filter(event)
    # if source field is not present
    if event.get(@source_field).nil?
        event.tag("#{@source_field}_not_found")
        return [event]
    end

    source_data = event.get(@source_field)

    # create empty hash to hold new result
    output = Hash.new()

    for item in source_data
        if item.key?(@key_field)
            new_key = item[@key_field]
            unless output.key?(new_key)
                output[new_key] = Array.new()
            end

            new_value = Hash.new()
            new_value["resource"] = item["resource"]
            new_value["granted"] = item["granted"]

            output[new_key].push(new_value)
        end
    end

    event.set(@destination_field, output)

    return [event]
end

## Validation tests

test "single entry in source" do
    parameters {{ "source_field" => "authinfo", "destination_field" => "result", "key_field" => "permission" }}
    in_event {{ "authinfo" => [{"resource" => "billingAccounts/019921-BE6AE6-562F1C", "permission" => "billing.resourceAssociations.create", "granted" => true, "resourceAttributes" => {}}] }}
    expect ("the source element is restructured") { |events|
        newelement = events.first.get("result")

        newelement["billing.resourceAssociations.create"][0]["resource"] == "billingAccounts/019921-BE6AE6-562F1C" &&
        newelement["billing.resourceAssociations.create"][0]["granted"] == true
    }
end

test "multiple items in source array" do
    parameters {{ "source_field" => "authinfo", "destination_field" => "result", "key_field" => "permission" }}
    in_event {{ "authinfo" => [{"resource" => "billingAccounts/019921-BE6AE6-562F1C", "permission" => "billing.resourceAssociations.create","granted" => true,"resourceAttributes" => {}}, {"resource" => "projects/suit-ai","permission" => "resourcemanager.projects.createBillingAssignment","granted" => true,"resourceAttributes" => {}}, {"resource" => "projects/suit-ai","permission" => "resourcemanager.projects.deleteBillingAssignment","granted" => false,"resourceAttributes" => {}}] }}
    expect ("the source element is restructured") { |events|
        newelement = events.first.get("result")

        newelement["billing.resourceAssociations.create"][0]["resource"] == "billingAccounts/019921-BE6AE6-562F1C" &&
        newelement["billing.resourceAssociations.create"][0]["granted"] == true &&
        newelement["resourcemanager.projects.createBillingAssignment"][0]["resource"] == "projects/suit-ai" &&
        newelement["resourcemanager.projects.createBillingAssignment"][0]["granted"] == true &&
        newelement["resourcemanager.projects.deleteBillingAssignment"][0]["resource"] == "projects/suit-ai" &&
        newelement["resourcemanager.projects.deleteBillingAssignment"][0]["granted"] == false
    }
end

test "multiple items in source array with same permission" do
    parameters {{ "source_field" => "authinfo", "destination_field" => "result", "key_field" => "permission" }}
    in_event {{ "authinfo" => [{"resource" => "billingAccounts/019921-BE6AE6-562F1C", "permission" => "billing.resourceAssociations.create","granted" => true,"resourceAttributes" => {}}, {"resource" => "projects/suit-ai","permission" => "billing.resourceAssociations.create","granted" => false,"resourceAttributes" => {}}, {"resource" => "projects/suit-ai","permission" => "resourcemanager.projects.deleteBillingAssignment","granted" => false,"resourceAttributes" => {}}] }}
    expect ("the source element is restructured") { |events|
        newelement = events.first.get("result")

        newelement["billing.resourceAssociations.create"][0]["resource"] == "billingAccounts/019921-BE6AE6-562F1C" &&
        newelement["billing.resourceAssociations.create"][0]["granted"] == true &&
        newelement["billing.resourceAssociations.create"][1]["resource"] == "projects/suit-ai" &&
        newelement["billing.resourceAssociations.create"][1]["granted"] == false &&
        newelement["resourcemanager.projects.deleteBillingAssignment"][0]["resource"] == "projects/suit-ai" &&
        newelement["resourcemanager.projects.deleteBillingAssignment"][0]["granted"] == false
    }
end

test "nonexistent source field" do
    parameters {{ "source_field" => "authinfo", "destination_field" => "result", "key_field" => "permission" }}
    in_event {{  "authinfo2" => {"resource" => "billingAccounts/019921-BE6AE6-562F1C", "permission" => "billing.resourceAssociations.create", "granted" => true, "resourceAttributes" => {}} }}
    expect("the event is tagged") { |events| events.first.get("tags")&.include?("authinfo_not_found") }
end
